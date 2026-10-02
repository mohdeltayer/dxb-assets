# Newsroom workflow (agreed 2 Oct 2026)

Mohammad reviewed an outside "Arabic gaming newsroom" brief on 2 Oct 2026
and approved these improvements. They sit on top of CLAUDE.md, which
still decides everything about voice, brands, accounts and timing.
Nothing here posts on its own, and posts already in Postiz stay as they
are.

## 1. Story ledger (`ledger.py`, `stories/`)

One JSON file per story; the fields are in `ledger.py`'s docstring, and
`story-template.json` is a filled example.

- **Before shortlisting:** `python3 newsroom/ledger.py find <words>`. A hit
  is an update, a follow-up or a duplicate, never a new story. Five
  outlets carrying one announcement are one story.
- **From shortlist on**, the story file holds:
  - sources, with their role and who they came through
  - each claim with its status
  - the drafts as shown, and the versions
  - timings, and media with where each file came from
- **After queuing:** `ledger.py sync` attaches the queue folders and the
  Postiz ids from the receipts.
- The 130 stories posted up to 1 Oct were backfilled from dxb-queue
  (`"backfilled": true`). Their grouping is by folder name and is rough:
  the Uncharted story shows as two.

## 2. Approval card

Every shortlisted story comes to him as a short card (`ledger.py card
<id>`):

- the title and its source (role, Dubai time, who it came through)
- ✓ confirmed and ~/? unconfirmed claims, with who says so
- one line on why it matters
- per account: lane, chip, proposed time and the text, English and
  Arabic side by side
- the media
- what changed since the version he last saw

The research stays behind the card. When he asks:

- **"Source?"**: the primary source, the original reporter if there is
  one, and the exact claim it supports. Never only an outlet's name.
- **"What changed?"**: the difference between the version he saw and
  this one.

## 3. Preflight and the approval marker (dxb-queue)

`dxb-queue/.github/scripts/preflight.py`, run by `publish.py` on every
pending folder; a folder that fails is not sent. It checks:

- **Account and timing:** the account id and platform, TikTok and
  YouTube refused while dropped, a scheduled type, a time at least
  2 minutes ahead.
- **Text:**
  - no em dash
  - every Arabic paragraph opens on an Arabic letter
  - no hashtags on X
  - the Instagram tag line starts `#ألعاب #أخبار_الألعاب` with exactly
    4 tags, and the caption stays within 2200 characters
- **Video:** h264 in yuv420p, Reels 1080x1920 with sound, 3 to 180
  seconds, no black opening frame, size.
- **Approval:** a marker whose fingerprint matches the folder as it
  stands.

Order of work:

1. Build in `drafts/`.
2. Run `python3 .github/scripts/preflight.py --no-approval drafts/<name>`
   and fix every error.
3. Show him the card.
4. After his "go" for that version and time:
   `python3 .github/scripts/preflight.py approve drafts/<name> --note "go 2 Oct 09:40"`.
5. Move the folder to `queue/` and dry-run `publish.py`.
6. Push, then run `ledger.py sync`.

Any edit after approval breaks the fingerprint and the folder is refused
until he has seen the new version. A re-encode that changes no content
(a codec fix after a rejection) still changes the bytes. Say what was
done and re-approve under the same go, noting it in `--note`.

The marker is written by the agent, so it guards against mistakes, not
against intent. The rule that only his "go" writes it is what makes it
mean anything.

On 1 Oct, 49 recent Digital Lounge videos were yuv444p, which Instagram
refused twice. Every video template now encodes yuv420p.

## 4. Verification rules

- Every claim is checked on its own. A source confirming the game and
  the date does not confirm the frame rate.
- Claim status: verified (the primary says it) / reported (a named
  outlet or journalist, no primary) / rumour / unverified / disputed /
  contradicted. Wording never lifts a claim up the ladder; the chip
  matches the weakest claim the post leans on.
- **Source chain:** ten articles citing one report are one source. Write
  "حسب تقرير لـ …" for the original reporter, never "تقارير متعددة",
  unless the sources are independent.
- **Sources disagree:** compare times, primary against secondary, exact
  wording, later edits and regional versions. If it stays unresolved,
  the claim is disputed and does not go out as fact.
- **Analysis is not a spec:** "حسب تحليل Digital Foundry" never becomes
  "أكدت الشركة". "Targets 60fps" stays a target (تستهدف), never "runs
  locked at" (تعمل بثبات).
- **Never infer** platforms from earlier entries, performance from
  hardware, exclusivity from a trailer's platform list, cancellation
  from silence, or confirmation from repetition. Missing means unknown.
- **Quotes:** «…» only for words the person said, translated faithfully
  and no more certain than the original. A paraphrase gets no quote
  marks. If a translated quote is shortened, it is still a quote of
  what was said, not a rewrite.
- **Subtitles:** transcript, then a check against on-screen text or the
  source, then the Arabic. Uncertain audio is flagged, never guessed.

## 5. Corrections

When a live post turns out wrong, he gets this at once, not at the next
sweep:

- what we published (account, time, the line)
- what is now known
- the source of the correction
- which accounts and platforms carry it
- the proposed correction (usually a reply under the post on X; a
  pinned comment or a corrected caption on Instagram)

He decides; live posts are not changed unless he asks. Both versions go
into the story's `corrections[]`, and the error type goes into the
glossary or these rules so it does not repeat.

- **Minor additions:** recorded in the ledger, posted only if worth a
  post.
- **A source that deletes or changes a statement:** find out what
  changed before assuming why.

## 6. Events

`events.md`: confirmed dates only, in Dubai time with the source's own
time zone. Undated shows stay "date unknown" and are watched for an
announcement. On show days, each announcement is captured as it lands
(game, type, platforms, date, trailer, official page). Platforms, dates,
prices and exclusivity are checked against the official page or press
release before they go out. Reminders before a show only when he wants
them.

## 7. Scout

Changes proposed for the end of the trial (report due 5 Oct) are in
`../notes/scout-proposals-2026-10-05.md`. Nothing changes in the scout
until he agrees.

## 8. Performance and experiments

`experiments.md` logs what has been tried, the evidence and the
decision. There are two baselines, one for Digital Lounge and one for
DXB-KNIGHT. No rule comes from one post or a few days. Numbers go into
each story's `metrics[]` at about 24 hours. Where they come from (by
hand, Postiz, or a paid tool such as Metricool) is his call. Engagement
never argues for a weaker label, a hidden "reported", a louder headline
than the source, or console-war framing.

## 9. Capabilities

`capabilities.md`: what the agent can and cannot use, so no session
assumes a tool it does not have.
