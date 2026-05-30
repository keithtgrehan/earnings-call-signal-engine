# ASR Execution Status

- Registered audio rows: 1
- Target case: `vz_2024_q4`
- Backend: `faster-whisper`
- Dependency status: `available_python_package`
- Run status: `complete`
- ASR complete rows: 1
- Segment rows: 249
- Cloud ASR used: false
- Raw ASR committed: false
- Install instructions: PYENV_VERSION=3.11.3 python3 -m pip install faster-whisper; download or place a local model such as Systran/faster-whisper-tiny outside the repo, then run PYENV_VERSION=3.11.3 python3 tools/run_local_asr_batch.py --backend faster-whisper --model /path/to/local/faster-whisper-model
