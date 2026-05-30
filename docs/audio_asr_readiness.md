# Audio ASR Readiness

Local ASR is optional and dependency-gated. Supported local backend names are `faster-whisper`, `whisper.cpp`, and `openai-whisper`.

Missing dependencies must report `dependency_missing`; they must not trigger cloud ASR or fail validation. Raw ASR text, when generated, belongs only under the Desktop workspace.
