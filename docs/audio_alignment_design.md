# Audio Alignment Design

Alignment metadata links ASR segments to registered transcript spans by `case_id`, audio SHA256, transcript SHA256, and span IDs. The repo stores alignment metadata only; raw ASR text and transcript body text stay outside git.
