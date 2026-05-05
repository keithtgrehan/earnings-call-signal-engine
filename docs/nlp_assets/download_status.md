# NLP Asset Download Status

Downloaded means the safe tooling cached a small public metadata/reference artifact. It does not imply raw training data availability unless explicitly stated.

## Status Counts

- `downloaded`: 1
- `gated`: 5
- `manual_required`: 24
- `skipped`: 41

## Downloaded Safe Cache Artifacts

- SEC company tickers JSON: `data/nlp_assets/cache/sec_company_tickers.json`

## Manual Or Gated Assets

- Loughran-McDonald Master Dictionary (`manual_required`): Site terms/manual review required before redistributing dictionary files.
- Financial PhraseBank (`manual_required`): Dataset card/license review required; do not redistribute without checking source terms.
- FINOS financial data / AI readiness references (`manual_required`): FINOS project-specific licenses vary; manual review required.
- Public earnings-call transcript dataset candidates (`gated`): Kaggle and vendor dataset licenses vary; often gated/manual.
- Stanford Sentiment Treebank (`manual_required`): Stanford dataset terms require manual review.
- DAIR.AI Emotion dataset (`manual_required`): Dataset card license review required.
- EmpatheticDialogues (`manual_required`): CC BY-NC 4.0; non-commercial restriction.
- Banking77 (`manual_required`): Dataset card/license review required.
- CLINC150 (`manual_required`): Dataset license/terms require review.
- Qasper (`manual_required`): Dataset license requires review; public research dataset.
- MS MARCO (`manual_required`): Microsoft dataset terms/manual review required.
- BEIR (`manual_required`): Benchmark wrapper; component dataset licenses vary.
- MultiWOZ (`manual_required`): Dataset license/versions require manual review.
- Switchboard (`gated`): LDC paid/restricted access.
- AMI Meeting Corpus (`manual_required`): AMI license/manual access terms require review.
- MeetingBank (`manual_required`): Repository/dataset license review required.
- SAMSum (`manual_required`): Dataset card/license review required.
- DialogSum (`manual_required`): Dataset license requires review.
- QMSum (`manual_required`): Dataset license/manual review required.
- Customer support public dataset candidates (`gated`): Kaggle licenses vary; gated/manual.
- YAKE (`manual_required`): GPL-3.0; license compatibility review required.
- openSMILE (`manual_required`): License/manual review required for some use cases.
- pyannote.audio (`gated`): MIT code; many pretrained models are gated on Hugging Face.
- TED-LIUM (`manual_required`): CC BY-NC-ND 3.0; non-commercial/no-derivatives restrictions.
- CMU-MOSEI (`manual_required`): Dataset license/manual request terms required.
- CMU-MOSI (`manual_required`): Dataset license/manual request terms required.
- AVEC challenges (`manual_required`): Challenge data terms vary; often manual/restricted.
- MELD (`manual_required`): Dataset license/manual review required; derived from TV content.
- IEMOCAP (`gated`): USC license/manual access; restricted.
