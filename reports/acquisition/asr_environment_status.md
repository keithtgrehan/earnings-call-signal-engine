# ASR Environment Status

- Status: `available`
- ffmpeg: `available`
- ffprobe: `available`
- Available backends: faster-whisper
- Cloud ASR used: false

## Install Commands

- `faster-whisper`: PYENV_VERSION=3.11.3 python3 -m pip install faster-whisper; place a local faster-whisper model outside the repo and run PYENV_VERSION=3.11.3 python3 tools/run_local_asr_batch.py --backend faster-whisper --model /path/to/local/faster-whisper-model
- `whisper.cpp`: Install whisper.cpp locally, build whisper-cli, and provide a local ggml model path.
- `openai-whisper`: PYENV_VERSION=3.11.3 python3 -m pip install -U openai-whisper
- `ffmpeg`: brew install ffmpeg
