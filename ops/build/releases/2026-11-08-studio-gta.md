# Release 2026-11-08, studio: «الطريق إلى GTA VI» series kit (day release, 8 Nov ~13:00 Dubai)
Previous: 2026-11-08 (release 2)   Merge commit: @@MERGE@@
Run: studio request studio-gta-vi-series (Mohammad, 8 Nov 2026; verbatim on the dxb-queue board). Date first: 19 Nov
2026 confirmed on Rockstar's GTA VI page (read 03:40Z) and Take-Two's fiscal Q1 2027 release (7 Aug 2026).

## Merged
- Series kit (branch studio/gta-series):
  1. templates/gta_intro.py: the series intro, 2.9 s. Chip «الحلقة N», title «الطريق إلى GTA VI» in the spectacle
     theme's azure to amber, «باقي N يومًا» counted from gta_intro.LAUNCH (19 Nov 2026), Rockstar's launch trailer
     25.15 to 27.18 s at 0.75x as a band with «المصدر: روكستار غيمز (Rockstar Games)», our own sound. Assets committed:
     templates/assets/gtavi/intro-band.mp4 (1.3 MB, Rockstar footage), intro-back.jpg.
  2. templates/sonic.py: flavour "gtavi" (the house motif D F# A E on a new warm 80s poly synth voice, synth80: two
     detuned band-limited pulse waves, no saw, no noise; B minor progression; tape-echo on the motif), palette synth80,
     arrangement for longer beds. Nothing licensed.
  3. templates/render_job.py: the job key "intro" picks its module by series. {"series": "gtavi", "days": N,
     "episode": E, "date": "YYYY-MM-DD"} is refused unless N equals the days from date to launch. Ocarina unchanged.
  4. notes/gta-series.md (plan, sources, ledger) and newsroom/context/gta-vi.md (verified facts).
  Switch: ON for jobs that carry the gtavi intro key; every other job renders exactly as before.
  Tests: self 10 (templates/test_gta_intro.py); parity: the neon, launch, retro and stats jingles and the neon 30 s bed
  byte-identical before and after (md5); server run 42463880307 on dxb-render-1: three intros with the Dubai font
  (16 s for three), frames checked (chip, title, count, credit; grid corner clear), the gtavi jingle and a 30 s bed.
  Branch: studio/gta-series (test branch studio/gta-series-test, never merged)

## Rollback
- git revert -m 1 @@MERGE@@, push to main. Episode jobs carrying the gtavi intro key then fail their check.
