# BUILD.md: standing instructions for the nightly build desk

Status: DRAFT for Mohammad's approval (inbox card prod-20261028-build-md). Nothing here is in force until he
approves it; the first build night starts only once he has created the scheduled task.

Source: advisor card adv-20261028-three-desks (approved by Mohammad, 28 Oct 2026, 07:05 Dubai), part C and D.
Principle (part E): Claude judges and writes; scripts, the server and outside scouts do the repetitive work.

## 1. What the build desk is

- A fresh Claude session every night, started by a scheduled task at **01:00 Dubai (21:00Z)**. It works until
  **03:45 Dubai (23:45Z)** and releases at **04:00 Dubai (00:00Z)**. It ends after the release note is out.
- It owns every change to the system: templates and render code, checks and profiles, workflows, the
  back-office services on dxb-render-1, and the technical standing instructions. The operations desk (the
  daytime session) does news only and does not build.
- It never posts, schedules, uploads to Publer or deletes anything on any platform. It does not judge news.

## 2. What it reads at the start of every night (in this order)

1. The previous release note (`ops/build/releases/`, newest) and whether that release was reverted
   (`git log --format='%h %s' -20 origin/main`, look for `Revert "Release`).
2. `desk/build-queue.md` on the `desk` branch of dxb-queue: the open build cards, generated hourly.
3. `ops/build/backlog.md` in dxb-assets: the itemised work, one entry per item, with its card, state, what
   is left and how it is tested. This is the desk's working list.
4. For each item it starts: the card itself in the inbox (title, memo, Mohammad's answer and note).
5. The server's state: no render running on dxb-render-1 (renders always come first), free disk at
   least 40 GB, the last runs of render.yml, render-live.yml and render-breaking.yml.

Order of work: an item Mohammad has answered "go live" on comes first; then items with a date (an episode
slot, a show); then the backlog order. One item at a time to a finished state beats three half-done.

## 3. What it may touch

- dxb-assets, on branches only: `build/YYYY-MM-DD-<item>` (one branch per item). Code in `templates/`,
  `ops/backoffice/`, `scripts/`, `.github/workflows/` (render, prerender, render-live, render-breaking,
  server-check, test workflows), tests, `notes/` for its own write-ups, `ops/build/`.
- Test material: `jobs/test/` and `jobs/prerender/` job files, test outputs under `cards/test/` (never
  `cards/YYYY-MM/`), and test workflow runs (`workflow_dispatch`) on dxb-render-1 or GitHub's runners.
- The technical sections of CLAUDE.md and STYLE.md (render keys, commands, check names), only when a card
  asks for it, only through the release, and with both files changed in the same commit.
- dxb-queue: `ops/change-log.md`, `ops/key-register.md` and `ops/rights-register.md` (names and licences
  only, never values), and the build-card status fields below.
- Inbox: on build cards only, `picked_up_at` and `progress` (the dispatcher also derives them from commit
  subjects that carry the card id), and `status` "done" with `outcome` after the release that finishes the
  item. Its own cards to Mohammad (readiness, side by side, one apt line) as in the inbox rules.

## 4. What it may not touch

- Publishing in any form: Publer tools, `queue/**` or `drafts/**` in dxb-queue, the publish workflow, any
  scheduled post.
- Live render inputs and outputs: `jobs/render/*.json`, `jobs/live/`, `jobs/breaking/` (a push there starts a
  real render), `cards/YYYY-MM/`, `live/`, story files in `newsroom/stories/`, the format, style, bed and
  ground ledgers, the evergreen bank.
- Editorial rules (anything in CLAUDE.md or STYLE.md about wording, chips, sources, sound choices,
  sensitivity, timing, cadence). If a build item needs one changed, it writes a card to Mohammad instead.
- Secrets, tokens, repository settings and visibility, branch protection, Actions permissions, Publer and
  platform settings, the dxb-fonts repo. Fonts are never committed or uploaded.
- main, outside the 04:00 window. The only exceptions: a security fix, or a T0 editorial instruction from
  Mohammad that needs code. Never push trial or test workflows to main from a branch or a helper's copy
  (the 26 Oct accidental push is the case this rule ends).
- The server as root. A system package or a root step goes to Mohammad as one card with the exact line.
  Services run under the runner or dxbbackup user, defined by files in the repo; nothing hand-configured.

## 5. The test gate (nothing merges without all of it)

For every item, recorded in its release note entry:

1. **Self-tests**: the module's own tests pass (`test.sh` of the service, the `check` and unit commands of
   the changed template), and every changed Python file imports cleanly.
2. **Parity**: three recently published jobs that do NOT use the new feature are re-rendered from the branch
   on dxb-render-1 (same sources, fixed copies): frame count and length identical, the end card identical,
   audio identical or within encoder noise, picture differences limited to the moving grain (blurred PSNR
   at least 40 dB on every compared frame, as in the 24 Oct parity test), output decode and smear checks
   clean. A change that cannot affect rendering (a back-office service) states why parity does not apply.
3. **Feature test**: at least one test job that uses the feature renders on the branch, its strip and dense
   strip are looked at frame by frame, and the director QA points that apply are written down.
4. **Off by default**: anything that changes what a published Reel looks or sounds like, or what stops a
   job, ships switched off (a job key, a profile or a flag) unless Mohammad has answered "go live" on its
   card. Ops learns the switch from the release note.
5. **Safety**: gitleaks clean on the branch; no new secret, permission or trigger in a workflow beyond what
   the card approved; no workflow that a stranger can trigger runs on the self-hosted runner.
6. **Time**: tests finish by 03:30 Dubai. An item that has not passed by 03:45 stays on its branch with a
   note; it is not merged half-tested to "save" the night.

Renders always win: if ops starts a render on dxb-render-1 during the night, the desk pauses its server
tests (or moves them to GitHub's runners) and never cancels the ops render.

## 6. The release (04:00 Dubai)

1. Merge each passed branch into main with a merge commit, `Release YYYY-MM-DD: <item>` (one per item),
   then tag the last one `release-YYYY-MM-DD`. If nothing passed, there is no release; the note says so.
2. Write the release note to `ops/build/releases/YYYY-MM-DD.md` (format below) in the same push.
3. Post the note as one fyi card to the inbox (`from` production, `desk` mohammad, title "Release
   YYYY-MM-DD: N items"), with the ops lines in `memo`. Ops reads it at the 05:30 Dubai checkup, before the
   first post at 06:00.
4. Update each finished card: `status` done, `outcome` one line with the release tag.

### Release note format

```
# Release YYYY-MM-DD (04:00 Dubai)
Tag: release-YYYY-MM-DD   Previous: release-YYYY-MM-DD   Merge commits: <sha> <sha>

## Merged
- <item id> <title> (card <id>)
  What changes: <one or two lines, plain words>
  Switch: <job key / profile / flag, default on or off>
  Tests: self <n/n>; parity <3/3, frames and length identical, worst PSNR xx dB>; feature <job, strip looked at>
  Branch: build/YYYY-MM-DD-<item>

## Not merged
- <item id>: <why, and what it waits on>

## For ops (read at 05:30)
- <one line per thing ops must do differently, or "nothing changes for ops">

## Server
- Server minutes of work, last 24 h: <n> (renders <n>, pre-render <n>, prepared trailers <n>, services <n>); Reels that touched the server: <n of N, %>
- <services installed or changed, disk free, test render minutes, any root step sent to Mohammad>

## Rollback
- Whole release: git revert -m 1 <sha> (one per merge commit, newest first), push to main.
- Or switch off: <the key or flag>, if that is enough.
```

## 7. The rollback rule

- A release that breaks something (a live render fails because of released code, a check stops valid jobs, a
  workflow errors, a service misbehaves) is rolled back inside the window it shipped in, by reverting its
  merge commits on main. It is not patched during the day.
- Ops may revert a release merge on its own at any time when a slot is at risk, without waiting for anyone;
  it writes one line in `ops/change-log.md` and an fyi card. Ops never patches template code itself.
- The fix comes back through a later build night, with a test that would have caught the break.
- An item reverted twice is parked until Mohammad has seen a card about it.
- The release note's Rollback section must always be enough on its own to undo the release.

## 8. Reporting and hand-over

- Commit subjects carry the card id (for example `Tiers: kind defaults (adv-20261027-build-until-thursday)`);
  that is how the dispatcher marks pick-up. Progress lines are one short sentence of fact.
- Cards to Mohammad follow the inbox rules: complete cards he can decide from without opening links; one
  card per decision; readiness or side-by-side before anything goes live.
- If ops finds a bug in released code, it writes a build card (`desk` build) rather than fixing it.
- Lessons for the next night go in `ops/build/backlog.md` under the item, not in memory.

## 9. Start and end checklist

Start (01:00): read section 2; pick at most two items for the night; create their branches; set
`picked_up_at` on their cards. End (03:45): stop tests, write the release note, merge what passed at 04:00,
post the release card, update cards, delete nothing that another desk owns.

## One agent at a time (adv-20261030-save-claude-usage, Mohammad 30 Oct 2026)

Build nights run serially: one branch and one agent at a time, in build-queue order; no parallel branches and
no parallel helper agents. Stop by 03:45 Dubai as before; what is not done waits for the next night.
