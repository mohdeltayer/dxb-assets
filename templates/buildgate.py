"""Build gate: the steps a Reel job must show before any render (adv-20261105-p2-audit-fixes, 5 Nov 2026).

Production 2's audit of 5 Nov found jobs rendered with no ledger search, no reel-check, no story file and no lane
chosen. This gate turns those steps into refusals. render_job.py runs it first for `check`, `text` and `run`, so the
pre-render check, render.yml, render-live.yml and render-breaking.yml all stop on it before any footage is fetched.

A job must carry:
  "story":       the story id; newsroom/stories/<id>.json must exist and hold
                   - "ledger_find": written by `python3 newsroom/ledger.py find <words> --record <id>`
                   - "sources": at least one entry with a "url"
                   - "first_report": where and when the story was first reported (text with a time)
                   - "source_type": "primary" or "secondary"
                   - "footage": what the Reel shows; stills must say why ("stills: <reason and sources tried>")
                   - "lane" (the account lane, as today) and "beat"
  "render_lane": "server" (the default: dxb-render-1, jobs/live/ and render-live.yml, or jobs/breaking/) or
                 "hosted" (GitHub's runner through jobs/render/ and render.yml) with "lane_reason"
  "reel_check":  newsroom/reel-check.md filled in, at least MIN_LINES answers, none of them "no": either a list of
                 {"line", "answer": "yes" | "n/a", "evidence"} or a dict {line: "yes: evidence" | "n/a: why"}
  "stills_reason": only for a stills job (template "stills", or every picture shot an image; adv-20261102-reel-checklist,
                 addendum of 3 Nov: footage first). {"why": one of STILLS_WHY, "tried": [the footage sources looked at]};
                 "tried" may be empty only for sales, business, people, delay or outage stories.

  "credits":     every footage shot (any shot that is not one of our "-gfx-" cards) inside at least one credit's
                 [first_shot, last_shot] (adv-20261030-download-automation-and-credits, Part B: every clip that is not
                 ours carries an on-screen credit for as long as it shows). Breaking and Famitsu jobs draw their own.

  "angle":       for a تقرير or تسريب job (its "label"), the story file's (or the job's) "angle" with "why_now" and
                 "what_it_means_here" (or "what_it_means"), each at least REPORT_MIN_WORDS words and not a restatement
                 of the headline (adv-20261107-context-in-reports, 9 Nov 2026: a report built on a sighting says what
                 the sighting usually means, the precedent, and what is not confirmed; if the brief cannot fill these,
                 the item is not a Reel).

  cover:         the first shot is never one of our "-gfx-" cards on the plain living ground, nor a logo plate alone:
                 a card that opens a Reel has the game's trailer or key art behind it ("ground_footage", the card's
                 own [file, start], or "ground_still"); otherwise open on footage, key art or a trailer frame
                 (adv-20261108-numbers-cards-grid item 2, 9 Nov 2026; render_job also reads a still cover's pixels).

  numbers ground: every "-gfx-" card sits on the game's own picture: "ground_footage" (its trailer, moving), the card's
                 own [file, start], or "ground_still" (its official key art, blurred and dimmed; numgfx 'still'
                 ground). The plain rotating ground is only for a chart of several games or a company's figures, and
                 then the job says so: "ground": "rotate" with "ground_reason" (adv-20261108-numbers-cards-grid item
                 3, build 9 Nov 2026).

  backdrop:      (release 2026-11-10) no plain ground on any Reel: "ground": "rotate" is refused, every card sits on
                 footage or art, and a card-led job carries "ground_footage" or "ground_still".
  evergreen:     a job with "post_kind": "evergreen" (or the دليل chip, or "bank") takes no news chip and no
                 «ليست خبرًا جديدًا» family in its headline, lines or captions' first line.
  built_by:      the building session; the director PASS must come from another (presubmit.py director --by).

  layout:        "layout": "showcase" carries "showcase_reason" naming one of its two cases, the trailer itself is
                 the news or the source fails the quality gate enlarged with no better copy (reel.showcase_reason).

Report only (printed, never a refusal): a credit covering footage that names no source («المصدر», «لقطات من»,
«الصورة»); a job without "decision_log" (adv-20261102-borrow-openmontage, part 2: per beat
the shot chosen and the alternatives, the crop decision, the music and why). The director reads it.

Jobs under jobs/test/ (examples and test renders) are not gated. There is no switch to turn the gate off.

    python3 templates/buildgate.py jobs/live/<name>.json      # prints the refusals, exit 1 when there are any
"""
import json
import re
import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
STORIES = REPO / 'newsroom' / 'stories'
MIN_LINES = 8
STORY_FIELDS = ('first_report', 'source_type', 'footage', 'lane', 'beat')
SERVER_DIRS = ('jobs/live/', 'jobs/breaking/', 'jobs/prerender/')
HOSTED_DIRS = ('jobs/render/', 'jobs/breaking/', 'jobs/prerender/')
STILL = ('.jpg', '.jpeg', '.png', '.webp')          # reel.STILL
STILLS_WHY = ('sales', 'business', 'people', 'delay', 'outage', 'no_footage')
STILLS_FREE = ('sales', 'business', 'people', 'delay', 'outage')   # no footage search needed (reel-check.md PICTURE)
REPORT_CHIPS = ('تقرير', 'تسريب')
REPORT_MIN_WORDS = 8
CARD_LED = ('storybeat', 'numbers', 'list', 'retro', 'edition', 'reviewscores', 'explainer', 'quote')  # our graphics or declared


def _rel(path):
    p = pathlib.Path(path).resolve()
    try:
        return p.relative_to(REPO).as_posix()
    except ValueError:                       # another clone or a scratch copy: keep the part from jobs/ on
        s = p.as_posix()
        i = s.rfind('/jobs/')
        return s[i + 1:] if i >= 0 else str(path).replace(os.sep, '/').lstrip('./')


def _answers(rc):
    """(answer, line) pairs from either reel_check shape."""
    if isinstance(rc, dict):
        for line, v in rc.items():
            yield (str(v.get('answer', '')) if isinstance(v, dict) else str(v)), str(line)
    elif isinstance(rc, list):
        for item in rc:
            if isinstance(item, dict):
                yield str(item.get('answer', '')), str(item.get('line', '?'))
            else:
                yield str(item), '?'


def is_stills_job(job):
    """True when the Reel's picture is stills: template "stills", or every non-graphics shot is an image."""
    if job.get('template') == 'stills':
        return True
    if job.get('template') in CARD_LED or job.get('kind') in ('famitsu', 'breaking'):
        return False
    pics = [sh[0] for sh in job.get('shots') or []
            if isinstance(sh, (list, tuple)) and sh and isinstance(sh[0], str) and '-gfx-' not in sh[0]]
    return bool(pics) and all(os.path.splitext(f)[1].lower() in STILL for f in pics)


def stills_problems(job):
    if not is_stills_job(job):
        return []
    r = job.get('stills_reason')
    if not isinstance(r, dict) or r.get('why') not in STILLS_WHY:
        return ['stills job: footage first. Add "stills_reason": {"why": ' + ' | '.join(STILLS_WHY) +
                ', "tried": [footage sources looked at]} or use official footage']
    if r['why'] not in STILLS_FREE and not [t for t in r.get('tried') or [] if str(t).strip()]:
        return ['stills job with why "no_footage": list the footage sources tried in "stills_reason": {"tried": [...]}']
    return []


SOURCE_WORDS = ('المصدر', 'لقطات من', 'الصورة')


def _footage_shots(job):
    return [i for i, sh in enumerate(job.get('shots') or [])
            if isinstance(sh, (list, tuple)) and sh and isinstance(sh[0], str) and '-gfx-' not in sh[0]]


def _credit_ranges(job):
    out = []
    for c in job.get('credits') or []:
        if isinstance(c, (list, tuple)) and len(c) >= 3:
            try:
                out.append((int(c[0]), int(c[1]), str(c[2])))
            except (TypeError, ValueError):
                continue
    return out


def credit_problems(job):
    if job.get('kind') in ('famitsu', 'breaking'):
        return []
    rng = _credit_ranges(job)
    # The WHERE AND HOW MUCH frame's own shot: designpass.py refuses a credit under the frame (one focus at a time,
    # memo of 24 Oct), so that shot carries the frame, with the credit on the shots either side (11 Nov 2026).
    fr = job.get('frame') if isinstance(job.get('frame'), dict) else {}
    framed = {int(fr['shot'])} if isinstance(fr.get('shot'), int) else set()
    bare = [i for i in _footage_shots(job) if i not in framed and not any(a <= i <= b for a, b, _ in rng)]
    if bare:
        return ['credits: footage shot%s %s %s no on-screen credit; add "credits": [[first, last, "المصدر: ..."]] '
                'covering every clip that is not ours' % ('s' if len(bare) > 1 else '', ', '.join(map(str, bare)),
                                                           'have' if len(bare) > 1 else 'has')]
    return []


def notes(job):
    """Report-only lines (never refusals)."""
    out = []
    if job.get('kind') not in ('famitsu', 'breaking'):
        rng = _credit_ranges(job)
        unsourced = [i for i in _footage_shots(job)
                     if any(a <= i <= b for a, b, _ in rng)
                     and not any(a <= i <= b and t.strip().startswith(SOURCE_WORDS) for a, b, t in rng)]
        if unsourced:
            out.append('credits: shots %s are covered only by credits that name no source (%s); report only'
                       % (', '.join(map(str, unsourced[:8])), ' / '.join(SOURCE_WORDS)))
    if not job.get('decision_log'):
        out.append('no "decision_log" (per beat: shot and alternatives, crop decision, music and why); the director '
                   'reads it (adv-20261102-borrow-openmontage); report only')
    return out


def _words(t):
    return [w for w in str(t or '').replace('\n', ' ').split() if w.strip('.,،:;«»"()')]


def report_angle_problems(job, story):
    """adv-20261107-context-in-reports: a تقرير or تسريب needs a real 'why now' and 'what it means for players'."""
    if str(job.get('label') or '').strip() not in REPORT_CHIPS:
        return []
    angle = story.get('angle') if isinstance(story.get('angle'), dict) else None
    angle = angle or (job.get('angle') if isinstance(job.get('angle'), dict) else {})
    head = set(_words(job.get('headline')))
    out = []
    for key, alts in (('why_now', ('why_now',)), ('what_it_means_here', ('what_it_means_here', 'what_it_means'))):
        val = next((angle.get(a) for a in alts if angle.get(a)), '')
        w = _words(val)
        if len(w) < REPORT_MIN_WORDS:
            out.append(f'report brief: angle "{key}" has {len(w)} words (at least {REPORT_MIN_WORDS}): say what the '
                       f'sighting usually means, the precedent and what is not confirmed, or it is not a Reel')
        elif head and len(set(w) & head) >= 0.8 * len(set(w)):
            out.append(f'report brief: angle "{key}" restates the headline; give the context instead')
    return out


def cover_problems(job):
    """adv-20261108-numbers-cards-grid item 2: the cover (first frame) is never a card on the plain ground."""
    sh = (job.get('shots') or [None])[0]
    if not (isinstance(sh, list) and sh and str(sh[0]).endswith('.png') and '-gfx-' in str(sh[0])):
        return []
    behind = (len(sh) > 1 and isinstance(sh[1], list)) or bool(job.get('ground_footage')) or bool(job.get('ground_still'))
    if behind:
        return []
    return ['cover: the first shot is a card on the plain living ground; put the game\'s trailer or key art behind it '
            '("ground_footage", the card\'s own [file, start], or "ground_still") or open on footage, key art or a '
            'trailer frame']


PLATE_NAME = re.compile(r'(^|[-_/])(logo|plate|wordmark)([-_.]|$)', re.I)


def plate_cover_problems(job):
    """adv-20261108-numbers-cards-grid item 2: a cover whose picture is a logo plate alone (by name; render_job reads the
    pixels of a still cover too)."""
    sh = (job.get('shots') or [None])[0]
    if isinstance(sh, list) and sh and PLATE_NAME.search(str(sh[0])):
        return [f'cover: the first shot {sh[0]} is a logo plate; open on footage, key art or a trailer frame']
    return []


PERSON_KINDS = ('quote', 'people', 'cast')     # kinds whose subject is a person; layoffs only with a subject_person
PERSON_OPEN = 0.05                              # the person window opens on frame 0 (seconds)


def single_game(story):
    """True when the story is about one game (its "game" is one title, not a list or empty)."""
    g = story.get('game')
    return isinstance(g, str) and bool(g.strip()) and not re.search(r'\s(?:and|و)\s|,|،', g)


def person_problems(job, story):
    """People stories show the person (adv-20261111-person-stories-gate, Mohammad 11 Nov 2026; the Harada Reel went out
    with no face and no name plate because "report" stood for the kind of story). The story file carries
    "subject_person": null or {"name", "role", "photo_source"}. When it is set, or the kind is quote, people or cast, the
    job carries "subject_person" (the same), a "person" entry opening on frame 0, and a kind other than report; with no
    licensed photo, "person_photo": "none" and "searched": [where] and the person entry's picture is their best-known work
    (the name plate with the role still shows). A report about one game takes the kind of what happened."""
    out = []
    if 'subject_person' not in story:
        out.append('story file: "subject_person" missing: null, or {"name", "role", "photo_source"} when a person is the '
                   'subject (adv-20261111-person-stories-gate)')
    sp = story.get('subject_person')
    if sp is not None and not (isinstance(sp, dict) and all(str(sp.get(k) or '').strip() for k in ('name', 'role', 'photo_source'))):
        out.append('story file: "subject_person" is null or {"name", "role", "photo_source"} with all three filled')
        sp = None
    kind = job.get('kind_news')
    if kind == 'report' and (sp or single_game(story)):
        import formats
        out.append('kind_news ' + formats.REPORT_IS_A_LABEL)
    if not (sp or kind in PERSON_KINDS):
        return out
    if sp and job.get('subject_person') != sp:
        out.append('job: "subject_person" is the story file\'s, copied (the server reads it for qc person_shown)')
    p = job.get('person') or []
    if not p:
        who = f"{sp['name']} ({sp['role']})" if sp else 'the speaker'
        out.append(f'person: a person is the subject ({who}): the job carries "person": [[photo, name, role, 0, t1, '
                   '{...}]], the photo box and name plate opening on frame 0 (people rule, 23 Oct; face on the cover, 24 Oct)')
    else:
        try:
            t0 = float(p[0][3])
        except (IndexError, TypeError, ValueError):
            t0 = None
        if t0 is None or t0 > PERSON_OPEN:
            out.append(f'person: the first person window opens at {t0} s; it opens on frame 0 (0.0), so the cover shows the face')
    if str(job.get('person_photo') or '').strip().lower() == 'none':
        if not [x for x in job.get('searched') or [] if str(x).strip()]:
            out.append('person_photo "none" needs "searched": [the press site, the organiser, licensed sources checked]')
    return out


BACKDROP_EXEMPT = ('storybeat', 'retro')        # the storybook page and the CRT den draw their own picture


def ground_problems(job):
    """No plain ground on any Reel (Mohammad, 9 Nov 2026 about 12:30 Dubai; release 2026-11-10): every "-gfx-" card sits
    on moving footage or art ("ground_footage", the card's own [file, start], or "ground_still"), and a card-led job
    carries a backdrop at job level. The living wave ground, the glow and the dotted grid are never a card's ground by
    themselves, so "ground": "rotate" is refused (it was the 9 Nov morning escape for multi-game charts)."""
    out = []
    if job.get('kind') in ('famitsu', 'breaking'):
        return out
    has = bool(job.get('ground_footage') or job.get('ground_still'))
    if job.get('ground') == 'rotate':
        out.append('ground: "rotate" is refused since 9 Nov (no Reel on the plain indigo ground, whatever the story): '
                   'give "ground_footage" (the company\'s latest trailer or press footage, the platform\'s own clip) or '
                   '"ground_still" (key art); with neither, the story is not a card-led Reel')
    cards = [sh for sh in job.get('shots') or [] if isinstance(sh, list) and sh and '-gfx-' in str(sh[0])]
    bare = [str(sh[0]) for sh in cards if not (len(sh) > 1 and isinstance(sh[1], list))]
    if bare and not has:
        out.append(f'ground: {", ".join(bare)} would sit on the plain living ground; give the game\'s art '
                   '("ground_footage": [file, start], or "ground_still": its key art)')
    if job.get('template') in CARD_LED and job.get('template') not in BACKDROP_EXEMPT and not has:
        out.append(f'backdrop: a card-led job ({job.get("template")}) carries "ground_footage" or "ground_still" '
                   '(moving footage or art, dimmed and credited); with neither, pick a footage-led template')
    return out


#: The «ليست خبرًا جديدًا» family (Mohammad, 9 Nov 2026; newsroom/editorial-memory.md 9 Nov, Elden Ring): an evergreen
#: piece never reads as news and never apologises for not being news. Approved openers: newsroom/names-ar.md.
EVERGREEN_BAD = re.compile(
    r'لي?س(?:ت)?\s+(?:هذا\s+|هذه\s+)?(?:ب?خبر[اًٌ]*\s*)?جديد[اًةٌ]*|خبر[اًٌ]*\s+قديم|قديم[ةٌ]?\b|من\s+زمان|'
    r'نعتذر|عذر[اًٌ]*|للتذكير\s+فقط|ليس(?:ت)?\s+بجديد')
EVERGREEN_CHIPS_BAD = ('جديد', 'رسمي', 'متوفر الآن', 'عاجل')


def is_evergreen(job):
    return str(job.get('post_kind') or '').lower() == 'evergreen' or job.get('label') == 'دليل' or bool(job.get('bank'))


def evergreen_problems(job):
    """kind:evergreen jobs: chip دليل (or the بالعربية plate), never a news chip; no «ليست خبرًا جديدًا» family in the
    headline, the lines or the first line of any caption the job carries (caption, x_text, threads_text)."""
    if not is_evergreen(job):
        return []
    out = []
    if job.get('label') in EVERGREEN_CHIPS_BAD:
        out.append(f'evergreen: chip {job.get("label")} reads as news; use دليل (or the بالعربية plate)')
    texts = [('headline', job.get('headline'))]
    lines = job.get('lines') or []
    for g in lines if isinstance(lines, list) else []:
        for x in (g if isinstance(g, list) else [g]):
            texts.append(('line', x if isinstance(x, str) else (x[0] if isinstance(x, list) and x else '')))
    for k in ('caption', 'x_text', 'threads_text'):
        if job.get(k):
            texts.append((k + ' first line', str(job[k]).strip().split('\n')[0]))
    for where, tx in texts:
        m = EVERGREEN_BAD.search(str(tx or ''))
        if m:
            out.append(f'evergreen: {where} says «{m.group(0)}»; an evergreen piece opens as a guide or a useful fact, '
                       'never as "not new" or an apology (approved openers: newsroom/names-ar.md, "Evergreen openers")')
    return out


def builder_problems(job):
    """Separate director (release 2026-11-10): the job names who built it, so the director PASS can be refused when the
    same session signs it (templates/presubmit.py director --by)."""
    if str(job.get('built_by') or '').strip() or job.get('kind') == 'breaking':   # T0 never waits on it
        return []
    return ['built_by missing: set "built_by": "<the building session, e.g. production-2>"; the director PASS must '
            'come from someone else (presubmit.py director ... --by <director>)']


def layout_problems(job):
    if job.get('layout') != 'showcase':
        return []
    try:
        import reel
        reel.showcase_reason(job.get('showcase_reason') or True)
    except ValueError as e:
        return [f'layout: {e}']
    except Exception:                          # reel needs the fonts; render_job checks it again on the runner
        if len(str(job.get('showcase_reason') or '').split()) < 5:
            return ['layout: showcase needs "showcase_reason" naming its case']
    return []


def problems(path, job):
    """The list of refusals for this job file (empty when it may render)."""
    rel = _rel(path)
    if rel.startswith('jobs/test/'):
        return []
    out = []

    lane = job.get('render_lane')
    if lane not in ('server', 'hosted'):
        out.append('render_lane missing: set "render_lane": "server" (default; jobs/live/ and render-live.yml) '
                   'or "hosted" with "lane_reason"')
    elif lane == 'server' and not rel.startswith(SERVER_DIRS):
        out.append(f'render_lane server: the job belongs in jobs/live/ (dispatch render-live.yml), not {rel}')
    elif lane == 'hosted':
        if not str(job.get('lane_reason') or '').strip():
            out.append('render_lane hosted needs "lane_reason" (why not the server)')
        if not rel.startswith(HOSTED_DIRS):
            out.append(f'render_lane hosted: the job belongs in jobs/render/, not {rel}')

    sid = job.get('story')
    if not sid:
        out.append('story missing: set "story": "<story id>" and write newsroom/stories/<id>.json first')
    else:
        f = STORIES / f'{sid}.json'
        if not f.exists():
            out.append(f'story file missing: newsroom/stories/{sid}.json')
        else:
            try:
                s = json.loads(f.read_text())
            except ValueError as e:
                s = {}
                out.append(f'story file unreadable: {e}')
            if not s.get('ledger_find'):
                out.append(f'no ledger search recorded: python3 newsroom/ledger.py find <words> --record {sid}')
            if not any(isinstance(x, dict) and x.get('url') for x in s.get('sources') or []):
                out.append('story file: no source with a url')
            for k in STORY_FIELDS:
                if not str(s.get(k) or '').strip():
                    out.append(f'story file: "{k}" missing')
            if s.get('source_type') and s.get('source_type') not in ('primary', 'secondary'):
                out.append('story file: "source_type" must be primary or secondary')
            out += report_angle_problems(job, s)
            out += person_problems(job, s)
            fo = str(s.get('footage') or '').strip().lower()
            if fo.startswith('stills') and len(fo) < 20:
                out.append('story file: stills need the reason and the footage sources tried')

    out += stills_problems(job)
    out += credit_problems(job)
    out += cover_problems(job)
    out += plate_cover_problems(job)
    out += ground_problems(job)
    out += layout_problems(job)
    out += evergreen_problems(job)
    out += builder_problems(job)

    rc = job.get('reel_check')
    if not rc:
        out.append('reel_check missing: fill newsroom/reel-check.md into the job as "reel_check"')
    else:
        pairs = list(_answers(rc))
        if len(pairs) < MIN_LINES:
            out.append(f'reel_check has {len(pairs)} answers; at least {MIN_LINES} lines of reel-check.md')
        noes = [line for a, line in pairs if a.strip().lower().startswith('no')]
        blank = [line for a, line in pairs if not a.strip()]
        if noes:
            out.append('reel_check answered no: ' + '; '.join(noes[:5]))
        if blank:
            out.append(f'reel_check has {len(blank)} unanswered lines')
    return out


def enforce(path, job):
    p = problems(path, job)
    if p:
        raise SystemExit('build gate refused ' + _rel(path) + ':\n  - ' + '\n  - '.join(p))
    if not _rel(path).startswith('jobs/test/'):
        print(f'build gate: ok ({job.get("render_lane")} lane, story {job.get("story")})', flush=True)
        for n in notes(job):
            print('build gate note:', n, flush=True)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    path = sys.argv[1]
    job = json.load(open(path))
    p = problems(path, job)
    for line in p:
        print('refused:', line)
    if not p:
        print('build gate: ok')
        for n in notes(job):
            print('note:', n)
    sys.exit(1 if p else 0)
