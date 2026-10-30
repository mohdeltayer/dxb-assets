"""Sound effects match the picture (advisor card adv-20261030-sfx-mismatch, Mohammad 30 Oct 2026, 19:09 Dubai).

Mohammad: some Reels carry sound effects that do not match what is on screen (the 19:00 Dubai Slay the Spire 2 Reel).
That Reel added nothing of ours: it ran one stretch of the trailer's own sound (0.5 s onward, the opening fight's
slashes, clangs and slams) under shots cut from 24 to 97 s of the same trailer, and the audio split, which would have
put each shot's own effects back under it, fell back because the stretch was effects-led (music 28.9%).

The rule, from the next render:
1. Footage keeps its own sound: under trailer or gameplay footage the only sound is the trailer's audio heard at the
   moment its picture comes from (or the music stem, with each shot's own effects from the same source moment: the
   audio split), or our bed. No added effects over footage, and no trailer effects from another moment.
2. Our effects belong to our own graphics only (a card entering, a counter ticking, a chip appearing, the end card),
   on the frame of that event; no effect without a visible event.
3. One effect family per Reel (the motion kit's motif blips); no whoosh or impact on footage cuts.
4. The edit plan lists every cue with its time and event (`plan`); `check` fails the job on a cue over footage or a
   trailer track whose effects would land under other shots; `guard` fails a runner render whose audio split fell
   back on such a track. A director who has measured the stretch as music or voice with no effects waives it with
   `"sfx_ok": "<reason, at least 10 characters>"` in the job.

What counts as in sync: every footage shot taken from the track's own file, with its source start within SYNC_TOL
seconds of the trailer time playing under it (track start + the shot's place on the Reel's timeline).
"""
import os

SYNC_TOL = 0.5          # seconds between a shot's picture time and the trailer sound under it
STING_KITS = ('scifi', 'fantasy')     # skins.py kits that mix a sting at the cut into the first line


def _track(job):
    tr = job.get('track')
    if isinstance(tr, (list, tuple)) and len(tr) >= 2 and tr[0] and tr[0] != 'bed':
        return tr[0], float(tr[1]), (tr[2] if len(tr) > 2 else None)
    return None


def _footage(f):
    return not os.path.splitext(str(f))[1].lower() in ('.jpg', '.jpeg', '.png', '.webp') and '-gfx-' not in str(f)


def offsets(job, starts):
    """Per footage shot: (index, file, picture time, trailer time heard, offset) against the track; None off-track."""
    tr = _track(job)
    if not tr:
        return []
    tf, ts, _ = tr
    out = []
    for i, (sh, t0) in enumerate(zip(job['shots'], starts)):
        f, st = sh[0], sh[1]
        if st is None or not _footage(f):
            continue
        heard = ts + t0
        out.append((i, f, float(st), round(heard, 2), None if f != tf else round(float(st) - heard, 2)))
    return out


def out_of_sync(job, starts):
    return [o for o in offsets(job, starts) if o[4] is None or abs(o[4]) > SYNC_TOL]


def split_skipped(job, profile=None):
    """Why the runner will not rebuild the sound per shot (tracksplit.py's own skips), or None."""
    if job.get('audio_split') is False:
        return 'job sets audio_split false'
    if job.get('speech_ok') or job.get('speech_keep'):
        return 'voiced track kept (speech_ok / speech_keep)'
    if (profile or job.get('profile')) == 'breaking' or job.get('label') == 'عاجل':
        return 'breaking profile'
    if job.get('skin') in STING_KITS:
        return f"skin {job['skin']}"
    return None


def plan(job, starts, lines=None):
    """The edit plan's sound-effect cues: [(time, cue, event, over)] with over 'footage' or 'graphic'."""
    cues = []
    shot_at = lambda t: max([i for i, s in enumerate(starts) if s <= t + 1e-6] or [0])
    if job.get('skin') in STING_KITS and lines:
        t = lines[0][1]
        f = job['shots'][shot_at(t)][0]
        cues.append((round(t, 2), f"{job['skin']} sting", 'cut into the first line', 'footage' if _footage(f) else 'graphic'))
    if job.get('kit') and 'chip' in job['kit'] and job.get('blips') is not False:
        cues.append((0.12, 'kit blip (press)', 'chip press on the cover', 'graphic'))
    if job.get('kit') and 'photobox' in job['kit'] and job.get('blips') is not False:
        cues.append((0.0, 'kit blip (wipe)', 'photo box opening', 'graphic'))
    if job.get('frame') and job.get('blips') is not False:
        cues.append((None, 'kit blips (press)', 'WHERE AND HOW MUCH frame: each logo pressing in', 'graphic'))
    cues.append((None, 'jingle', 'end card', 'graphic'))
    return cues


def check(job, starts, lines=None, profile=None):
    """Raise ValueError on a cue over footage or on a trailer track whose effects would land under other shots."""
    if job.get('sfx_ok') and len(str(job['sfx_ok']).strip()) >= 10:
        print(f"sfx: waived ({job['sfx_ok']})", flush=True)
        return
    bad = []
    cues = plan(job, starts, lines)
    for t, cue, event, over in cues:
        print(f"sfx cue: {'end' if t is None and cue == 'jingle' else ('event' if t is None else '%.2f s' % t)} "
              f"{cue}: {event} ({over})", flush=True)
        if over == 'footage':
            bad.append(f'{cue} at {t} s sits over a footage shot ({event}); our effects belong to our graphics only')
    oos = out_of_sync(job, starts)
    if oos:
        why = split_skipped(job, profile)
        desc = '; '.join(f"shot {i} {f} @{st}" + (' (another file)' if off is None else f' hears {heard} s ({off:+.1f} s)')
                         for i, f, st, heard, off in oos[:6])
        if why:
            bad.append(f'trailer sound under shots from other moments ({desc}) and no audio split ({why}): its effects '
                       'would not match the picture; take the shots from the track\'s own seconds, use a music-led '
                       'stretch measured with no effects (sfx_ok), or our bed (track "bed")')
        else:
            print(f'sfx: {len(oos)} shot(s) off the track\'s own seconds ({desc}); the audio split must apply, '
                  'or the runner stops (guard)', flush=True)
    if bad:
        raise ValueError('sound effects do not match the picture (adv-20261030-sfx-mismatch):\n' + '\n'.join(bad))


def guard(job, rec, starts):
    """After the runner's audio split: an out-of-sync trailer track that kept its mixed sound fails the job."""
    if rec.get('applied') or not _track(job):
        return
    if job.get('sfx_ok') and len(str(job['sfx_ok']).strip()) >= 10:
        return
    oos = out_of_sync(job, starts)
    if oos:
        raise ValueError(f"audio split not applied ({rec.get('reason')}) on a trailer track under {len(oos)} shot(s) "
                         "from other moments: the trailer's effects would not match the picture "
                         '(adv-20261030-sfx-mismatch). Take the shots from the track\'s own seconds, a music-led '
                         'stretch (sfx_ok with the measure), or our bed.')
