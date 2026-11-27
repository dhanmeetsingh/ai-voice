import json
import subprocess
import tempfile
import wave
from datetime import datetime, timedelta, timezone
from pathlib import Path

import sounddevice as sd ##take sound from device
from faster_whisper import WhisperModel ##convert speech to text
from ollama import Client ##apna llm
from piper import PiperVoice ##convert text to speech

ROOT = Path(__file__).resolve().parent
VOICE_PATH = ROOT / "voices" / "en_US-lessac-medium.onnx"
MODEL = "qwen2.5:3b"
SAMPLE_RATE = 16_000
RECORD_SECONDS = 7
DEMO_PROMPT = "What time is it now?"


def get_current_time(minutes_from_now: int = 25) -> str:
    """Read the laptop's local time and optionally calculate a session end time.

    Args:
        minutes_from_now: Session duration in minutes. Defaults to 25.
    """
    now = datetime.now(timezone.utc)
    end = (now + timedelta(minutes=minutes_from_now)).astimezone()
    return json.dumps({
        "local_time": now.astimezone().isoformat(timespec="seconds"),
        "session_minutes": minutes_from_now,
        "session_end": end.isoformat(timespec="seconds"),
    })


def ask_ollama(client: Client, transcript: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "Give a short, natural spoken reply. For questions about the "
                "current time, call get_current_time. When asked when a session "
                "will end, pass its duration as minutes_from_now. The tool "
                "defaults to the demo's 25 minutes. Use the "
                "local_time and session_end returned by the tool in your reply. "
                "Speak the hour and minute for each time."
            ),
        },
        {"role": "user", "content": transcript},
    ]
    for _ in range(4):
        reply = client.chat(
            model=MODEL,
            messages=messages,
            tools=[get_current_time],
            options={"temperature": 0, "num_predict": 160},
        ).message
        if not reply.tool_calls:
            if reply.content and reply.content.strip():
                return reply.content.strip()
            raise RuntimeError("Ollama returned an empty reply.")

        messages.append(reply)
        for call in reply.tool_calls:
            name = call.function.name
            args = call.function.arguments
            print(f"Tool request: {name}({json.dumps(args)})", flush=True)
            if name != "get_current_time":
                raise RuntimeError(f"Unexpected tool: {name}")
            result = get_current_time(**args)
            print(f"Tool result: {result}", flush=True)
            messages.append({"role": "tool", "tool_name": name, "content": result})

    raise RuntimeError("Ollama did not finish after four turns.")


def main():
    print("Loading local speech models…", flush=True)
    whisper = WhisperModel(
        "base.en", device="cpu", compute_type="int8", local_files_only=True
    )
    voice = PiperVoice.load(VOICE_PATH)
    client = Client(host="http://127.0.0.1:11434", trust_env=False)

    print(f"Say: {DEMO_PROMPT}")
    input("Press Enter to record… ")
    print(f"Mic: recording for {RECORD_SECONDS} seconds…", flush=True)
    try:
        audio = sd.rec(
            RECORD_SECONDS * SAMPLE_RATE,
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocking=True,
        )
    except sd.PortAudioError as error:
        raise SystemExit(
            f"Mic error: {error}. Check macOS Sound Input and microphone permissions."
        ) from error
    segments, _ = whisper.transcribe(audio[:, 0], language="en", vad_filter=True)
    transcript = " ".join(segment.text.strip() for segment in segments).strip()
    print(f"Transcript: {transcript or '(no speech detected)'}", flush=True)
    if not transcript:
        return

    reply = ask_ollama(client, transcript)
    print(f"Final reply: {reply}", flush=True)
    with tempfile.TemporaryDirectory() as directory:
        wav_path = Path(directory) / "reply.wav"
        with wave.open(str(wav_path), "wb") as wav_file:
            voice.synthesize_wav(reply, wav_file)
        print("Playback: playing the reply…", flush=True)
        subprocess.run(["/usr/bin/afplay", str(wav_path)], check=True)


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nStopped.")
