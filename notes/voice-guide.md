# Voiceover: how he records, what the preset does (draft, 2 Oct 2026)

The aim: every Digital Lounge voiceover sounds like the same broadcast
read, close to the Emirati news host in `voice-reference-2026-10-02.md`,
and still his own voice. He records to the rules below; `templates/voice.py`
does the rest the same way every time. Nothing here is posted without his
"go"; a voiced Reel is a draft like any other.

## Before recording

- **Room:** indoors, door shut, AC and fans off for the take. Soft
  furnishings help (a bedroom or a car parked in a garage is better than
  a tiled room). Never a moving car: the preset can clean it, but the
  voice loses body.
- **Phone:** iPhone Voice Memos with Settings > Voice Memos > Audio
  Quality set to Lossless. Phone a hand-span (about 20 cm) from the mouth,
  slightly to one side so breath does not hit the mic. Same distance for
  the whole take.
- **Mouth:** a sip of water a minute before; no dairy or sweet drinks just
  before. Lip balm helps against lip smacks.
- **Script:** the timed script from `notes/voice-scripts/`, one line per
  on-screen sentence, with the reading notes (vowels on numbers, how the
  English names are said).

## While recording

- **Slate:** say the story and take number first ("GTA, take one"), wait
  two seconds, then read. The preset trims the slate area by the pauses;
  say which take to use.
- **Pace:** about 100 words a minute, the host's pace. Unhurried; the
  pauses are fixed later, so do not rush them and do not hold them long.
- **Shape:** stress the key word in each line (the name, the number, the
  date) and let the line fall at the full stop. Formal Arabic, with
  English names said as an Arabic speaker says them.
- **Mistakes:** do not stop. Pause, then read the whole line again. The
  edit keeps the last clean read of each line.
- **Takes:** two full takes are enough.

## What the preset does (python templates/voice.py raw.m4a out)

1. AI denoise (or `--rebuild`, the stronger studio rebuild).
2. Mouth noise between phrases (lip smacks, swallows, breaths) down 30 dB;
   clicks inside words softened.
3. Pauses set to house values: 0.45 s between phrases, 0.75 s between
   sentences, 0.25 s at the start and end. Gaps under 0.3 s stay.
4. Tone: broadcast setting (less boom and boxiness, softer top, de-essed,
   compressed 5:1), -16 LUFS, peaks at -1.5 dB.
5. A faint room tone 30 dB under the voice through the pauses, so it never
   drops to dead silence.
6. A report against the host: tone per band, crest, pauses before and
   after. It aims about halfway to the host's tone, because the host clip
   is a recording of TV and already darker than the studio sound.

Under a Reel, the trailer's own sound drops about 18 dB under the voice
and comes back up in the pauses and on the end card.

## What it cannot fix

- Words lost under noise, or a muffled read through a hand or a pocket.
- Echo from a bare room (it can reduce it, not remove it).
- Pace and stress: the preset fixes the gaps between phrases, not the
  speed or the emphasis inside them.
- Retakes in the middle of a line: re-read the whole line.

## Still to agree

- Whether he wants the stronger `--rebuild` by default (clearer, a little
  less natural) or the plain denoise (default now).
- Room tone level (30 dB under the voice now; the host's is 26).
- First real indoor take to tune the tone against, then this guide stops
  being a draft.
