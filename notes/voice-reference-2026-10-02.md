# Voice reference 1: Emirati TV news host (2 Oct 2026)

Mohammad shared a 22 second clip of an Emirati news host reading a story
(Emirates' new Dubai to Helsinki route). It is a reference only: the clip
is not kept in the repo and none of its audio is used. Measured against
his car stress-test recording (`car-test-*`, 2 Oct), after the AI rebuild
and the mouth-noise fix.

## What the host does

**Script** (faster-whisper medium transcript, spelling corrected):

> تعزيزًا لشبكة رحلاتها التي تربط قارات العالم، دشّنت طيران الإمارات الخط
> المباشر الجديد من دبي إلى هلسنكي في فنلندا، بطائرة إيرباص A350، بواقع
> رحلة مباشرة يوميًا. تفاصيل أوفى مع موفدنا إلى هلسنكي يوسف كانو.

- Formal Arabic (فصحى) throughout, although the host is Emirati and the
  channel local. Dialect is not what makes it sound local; the delivery is.
- Shape: a short context clause first (تعزيزًا لـ…), then a verb-first
  sentence with the news (دشّنت…), then one detail per phrase (route,
  aircraft, frequency), then a hand-off line (تفاصيل أوفى مع…).
- English names are said in Arabic phonology (إيرباص A350), not switched
  into an English accent.

**Delivery**

| | Host | His recording (car test) |
|---|---|---|
| Pace | about 100 words a minute | about 90 |
| Pauses | 0.4 to 0.5 s between phrases, about 1 s once after the opening clause | 0.8 to 1.9 s (unscripted, in a car) |
| Pitch | median 140 Hz, 10.7 semitones of range | median 145 Hz, 9.5 semitones |
| Peak to average (crest) | 7.2 dB (broadcast compression) | 8.7 to 9.0 dB |
| Silence between phrases | a steady room tone 26 dB under the voice | 56 to 64 dB under (dead silent) |

His voice sits in the same register as the host's, so the reference fits.
The differences are delivery (shorter, even pauses; a little more pitch
movement on the key word of each phrase) and the processing.

**Tone** (average spectrum while speaking, dB relative to 630 to 1250 Hz)

| Band (Hz) | 80-160 | 160-315 | 315-630 | 1.25k-2.5k | 2.5k-5k | 5k-10k | 10k-16k |
|---|---|---|---|---|---|---|---|
| Host | -8.1 | -4.3 | +2.7 | -7.8 | -14.3 | -25.2 | -35.5 |
| His studio v2 | +3.3 | +6.9 | +5.4 | -0.6 | -1.3 | -3.7 | -19.0 |
| His broadcast v3 | -0.2 | +4.1 | +5.2 | -2.7 | -5.9 | -8.1 | -23.1 |

Studio v2 was boosted at both ends: heavy lows (the car and phone
proximity) and very bright highs from the AI rebuild plus the presence
lift. The host is lean in the lows and smooth on top. The clip is a
screen recording of broadcast TV, which darkens the top a little, so v3
goes about halfway towards it rather than all the way.

## Settings: broadcast v3

After the AI rebuild (or denoise) and `mouthfix.py`:

```
highpass=f=110,lowshelf=f=220:g=-6,equalizer=f=300:t=q:w=1.0:g=-4,
equalizer=f=480:t=q:w=1.0:g=-1.5,equalizer=f=1000:t=q:w=1.4:g=-1.5,
highshelf=f=2000:g=-6,deesser=i=0.3:m=0.5:f=0.5,
acompressor=threshold=-30dB:ratio=5:attack=4:release=90:makeup=3,
loudnorm=I=-16:TP=-1.5:LRA=6
```

The words survive (speech recognition reads the same sentence as v2).
Not yet tried: leaving a faint room tone between phrases instead of
silence, which is part of why the host sounds natural.

## For a Digital Lounge voiceover

1. Write it like the host: context clause, verb-first news, one fact per
   phrase, a closing line that sends readers on (the post, the end card).
2. Read at about 100 words a minute with pauses of about half a second.
   Lift the key word in each phrase (the name, the number, the date).
3. Record close but off-axis, in a quiet room, a sip of water first.
4. Process: denoise or AI rebuild, mouth fix, broadcast v3.

Still open: whether voiceovers ever use dialect. The written posts stay
formal; this reference supports formal Arabic for voice too.
