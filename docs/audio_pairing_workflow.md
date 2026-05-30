# Audio Pairing Workflow

Audio is a support layer. A transcript remains canonical, and an audio asset can only become retrieval-ready after a registered transcript exists for the same `case_id`, local ASR text exists, and ASR segments are aligned to transcript spans.

The default pair states are `candidate`, `partial`, `matched`, `matched_review_required`, and `rejected`. Prepared-only audio must use `matched_review_required` even when transcript and audio files are both present.
