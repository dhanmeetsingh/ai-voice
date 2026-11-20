# Local voice agent

Press Enter and ask “What time is it, and when would a 25-minute study session end?” The demo records seven seconds of mono audio at 16 kHz, transcribes it with Faster Whisper, and sends the transcript to Qwen2.5 through Ollama. When Qwen2.5 calls `get_current_time`, Python reads the Mac’s clock and calculates the end time from that same reading. Piper speaks Qwen2.5’s final reply through the Mac’s default audio output.

## Set up on macOS

1. Install Python 3.12 (`brew install python@3.12` if you use Homebrew) and the [Ollama macOS app](https://ollama.com/download/mac). Open Ollama and complete its CLI setup so `ollama` is available in the VS Code terminal. Keep Ollama running.
2. Open this folder in VS Code. In its integrated terminal, run these one-time setup commands with internet access.

   ```sh
   python3.12 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt
   ollama pull qwen2.5:3b
   .venv/bin/python -c 'from faster_whisper.utils import download_model; download_model("base.en")'
   .venv/bin/python -m piper.download_voices --download-dir voices en_US-lessac-medium
   ```

   Faster Whisper uses the Hugging Face cache for the same macOS user. Piper keeps its `.onnx` and `.onnx.json` files in `voices/`. Qwen2.5 3B is about 1.9 GB. [Qwen2.5 model page](https://ollama.com/library/qwen2.5:3b)

3. Allow microphone access if macOS prompts during the first recording. If access was denied, go to **System Settings → Privacy & Security → Microphone**, enable **Visual Studio Code** (or **Terminal** if you run it there), then restart that app. In **System Settings → Sound**, select the microphone under **Input** and the Mac speakers under **Output**. [Apple microphone permissions](https://support.apple.com/guide/mac-help/control-access-to-your-microphone-mchla1b1e1fe/mac)

## Run the demo

From the `local-voice-agent` folder in the VS Code terminal:

```sh
.venv/bin/python main.py
```

Wait for the prompt, press Enter, and start speaking when `Mic: recording` appears. Check the transcript, the `get_current_time` request, and the printed tool result against the times in the spoken reply. The tool defaults to 25 minutes if the request omits the duration. The app exits after playback. Run the same command for another take.

After setup, the demo can run with Wi-Fi off. Faster Whisper loads cached files, Piper loads the downloaded voice, and Python connects to Ollama at `127.0.0.1:11434`.
