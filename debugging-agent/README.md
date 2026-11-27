# AI Debugging Agent

A small Python agent that reads a fictional application log, looks up its error code, and saves a Markdown report. Ollama decides which tool to request. Python validates the request, executes the tool, and sends the result back as a message. The terminal shows those observable exchanges.

## Setup on a Mac

Install Python 3.12 or newer and [Ollama](https://ollama.com/download/mac). Open Ollama so its local server is running. From `debugging-agent`, run:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
ollama pull qwen2.5:3b
```

## Run

```sh
.venv/bin/python main.py
```

The user request is built into the demo. Each run replaces `reports/debug_report.md` when the save tool succeeds. The report should cite the observed pool saturation and timeouts, identify pool exhaustion as a likely explanation, and propose checks for why connections stayed busy.

The model is served on localhost. Tool arguments contain only an error code or report text. Python chooses the input files and report path, bounds the log read, and caps the conversation at six model turns. The Ollama client uses a 45-second HTTP timeout. See the [Ollama tool-calling documentation](https://docs.ollama.com/capabilities/tool-calling) for the message format.

## Tests

```sh
.venv/bin/python -m unittest discover -s tests -v
```

The tests use temporary files and run without an Ollama server.
