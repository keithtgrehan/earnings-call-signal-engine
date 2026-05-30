# ASR Environment Status

- Status: `available`
- ASR ready status: `dependency_missing_model`
- ffmpeg: `available`
- ffprobe: `available`
- faster-whisper model: `missing` ``
- Available backends: faster-whisper
- Cloud ASR used: false

## Install Commands

- `faster-whisper`: PYENV_VERSION=3.11.3 python3 -m pip install faster-whisper; set FASTER_WHISPER_MODEL_PATH or place a local model under /Users/keith/Desktop/earnings calls 100 samples/_models/faster-whisper/; then run PYENV_VERSION=3.11.3 python3 tools/run_local_asr_batch.py --backend faster-whisper --model tiny
- `whisper.cpp`: Install whisper.cpp locally, build whisper-cli, and provide a local ggml model path.
- `openai-whisper`: PYENV_VERSION=3.11.3 python3 -m pip install -U openai-whisper
- `ffmpeg`: brew install ffmpeg
