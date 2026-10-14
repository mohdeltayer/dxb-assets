# Voice clone trial (advisor, 14 Oct 2026)

Synthesised reads in Mohammad's own voice: Chatterbox Multilingual (Resemble
AI, MIT, Arabic listed), cloned zero-shot from the cleanest 30 s of his own
recording. Pass: he accepts two of the three Reels; then one trial under the
next numbers Reel through `reel(..., voice=)` with the existing ducking.
Nothing synthesised is posted without his "go".

## What he records (per notes/voice-guide.md)

- About 20 minutes of MSA news reads, in one sitting: one mic, one room, the
  same distance for the whole take. 48 kHz WAV if the app offers it (Voice
  Memos Lossless is fine; it is converted here).
- News register, the host's pace (about 100 words a minute), formal Arabic,
  English names said as an Arabic speaker says them. Varied material: a few
  of our own captions, a few headlines, numbers, dates, prices, company names.
- No slate needed for this one; a pause of a few seconds between pieces.
- The cleanest 30 s is chosen by `voice.py ref`; the rest stays as material
  for a later fine-tune if the zero-shot clone passes.

## The six reads

Three published Reels, headline plus lines, rendered twice each: the raw text
(Latin names left as written) and after diacritisation (Mishkal, with the
names fixed from the glossary's "Names as read aloud"). Texts in
`2026-10-14-clone-trial.json`; `voice.py trial <ref.wav> <that json> <outdir>`
writes the six WAVs and `trial-log.md` with the CPU seconds per read.

1. `gt7-spec-iv-live-dualsense-gt-edition` (14 Oct, split, gold)
2. `ubisoft-redlynx-closure-proposal` (14 Oct, trailer)
3. `epic-abu-dhabi-unreal-educators` (14 Oct, split; a Gulf story with Arabic
   institution names)

## Judgement

For each pair: does it sound like him, is the Arabic read as news (stress on
the name, the number, the date), are the names right, which of raw and
diacritised reads better. Two of three accepted is a pass; which text form
wins decides the default. Then one Reel.

## Status

- 14 Oct: code (`templates/voice.py` ref, tashkeel, clone, trial), the setup
  script (`templates/voice_setup.sh`), the scripts and the glossary names
  section are in. The install waits on disk (about 5.5 GB for the venv and
  the weights; the container has about 460 MB free) and the clone on his
  recording.
