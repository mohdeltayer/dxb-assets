# Nightly backup mirror for dxb-render-1

A second backup copy of the three GitHub repos, kept on the render server next to the Backblaze
backup that dxb-queue's `backup.yml` already makes. It runs as its own user, `dxbbackup`, at the
lowest priority, and never touches the `runner` user, the render workflow or the publish flow.

## What it does

Every night at 05:00 Dubai (01:00 UTC), and again at 06:30 Dubai only if the first run was skipped:

1. Waits while a render is active (a process whose command line contains `render_job.py` or
   `Runner.Worker`), up to 30 minutes; then skips with exit 75 and the timer tries again at 06:30.
   Skipped on both tries raises a low-priority alert; the 09:00 check below catches the rest.
2. Pulls this folder's own repo (`~/dxb-assets`, `git pull --ff-only`), so the scripts and the unit
   files update themselves from the repo. Changed units are copied to `~/.config/systemd/user/`.
3. Mirrors `mohdeltayer/dxb-assets`, `dxb-queue` and `dxb-fonts`: `git clone --mirror` the first
   time, `git remote update --prune` after that. `gc` is off on the mirrors on purpose.
4. Exports, straight from the mirrors with `git archive` (no checkout, no media):
   * dxb-assets: `templates/assets/format-ledger.json`, `newsroom/corrections.md`, and the text files
     of `cards/` (the `*-publer.json` published log and similar; mp4, jpg and png are never exported);
   * dxb-queue: the text files of `ops/` (key and rights registers, change log, heartbeat, backups
     notes), `queue/**` and `drafts/**` `job.json` and `receipt.json`, and `.github/workflows/*.yml`;
   * from both: any rights or key register file and any Publer media index file, if one exists;
   * dxb-fonts: nothing (licensed fonts; the mirror holds them).
   A file is left out, and only its name recorded in `export/SKIPPED.txt`, when it is over 5 MB,
   looks like a token or private key, or contains the live token or ntfy topic value.
5. Takes a snapshot `~/mirror/snapshots/YYYY-MM-DD` (Dubai date) with hard links: the git files are
   linked to the live mirror, the exports to the previous snapshot (`rsync --link-dest`). A snapshot
   costs only what is new. A second run the same day (a `full` run) is kept as
   `YYYY-MM-DD_HHMM` and never replaces the night's snapshot. The newest 14 days are kept.
6. Writes the heartbeat and sends one line to ntfy: success (low priority) or failure (high).

Hard floor: before every write step, and every 15 seconds while git is copying, free space on the
backup filesystem is checked. If it would drop under 40 GB the run stops, kills git, sends an urgent
alert and leaves a partial clone out of the way (`.name.git.partial` is deleted on the next try).

A second timer at 09:00 Dubai (`mirror.sh heartbeat-check`) alerts if the last success is older than
26 hours, so a missed night or a dead timer cannot pass silently.

## Layout

```
~/mirror/git/<repo>.git        the live mirrors (bare)
~/mirror/snapshots/<date>/     git/ (hard links), export/, refs/<repo>.txt, MANIFEST.txt
~/mirror/state/                backup.log, last-success*, last-run, lock, export-build/
```

## One-time root steps (Mohammad)

As root on dxb-render-1. The user line is the one already agreed; the rest creates the two files.

```
apt-get install -y git rsync curl util-linux procps
useradd --create-home --shell /bin/bash dxbbackup && passwd -l dxbbackup && loginctl enable-linger runner dxbbackup
install -d -m 0750 -o root -g dxbbackup /etc/dxb-backup
install -m 0640 -o root -g dxbbackup /dev/null /etc/dxb-backup/github-token
install -m 0640 -o root -g dxbbackup /dev/null /etc/dxb-backup/ntfy-topic
nano /etc/dxb-backup/github-token     # paste the token on one line, save
nano /etc/dxb-backup/ntfy-topic       # paste the topic name on one line, save
ls -l /etc/dxb-backup                 # both files: -rw-r----- root dxbbackup
```

* `github-token`: a fine-grained personal access token, owner `mohdeltayer`, repositories
  `dxb-assets`, `dxb-queue` and `dxb-fonts`, permissions Contents: Read-only (Metadata read comes
  with it), with an expiry date. Read-only is all the mirror needs. Add it to `ops/key-register.md`
  (name, purpose, where it lives, rights, expiry; never the value).
* `ntfy-topic`: the same topic the stall alarm uses (`NTFY_TOPIC` in dxb-queue's
  `stall-alarm.yml`). The script sends it to curl on stdin and never prints it.

## Bootstrap (as dxbbackup, through root's sudo)

While dxb-assets is public:

```
sudo -iu dxbbackup bash -c 'git clone --depth 1 --filter=blob:none --sparse https://github.com/mohdeltayer/dxb-assets.git ~/dxb-assets && cd ~/dxb-assets && git sparse-checkout set ops/backoffice && ops/backoffice/backup/install.sh'
```

Once dxb-assets is private (and the token file exists), use the same credential helper the script
uses, so the token is read from the file by git itself and appears in no command line:

```
sudo -iu dxbbackup bash <<'EOT'
export GIT_TERMINAL_PROMPT=0 DXB_TOKEN_FILE=/etc/dxb-backup/github-token
export GIT_CONFIG_COUNT=2 GIT_CONFIG_KEY_0=credential.helper GIT_CONFIG_VALUE_0=
export GIT_CONFIG_KEY_1=credential.https://github.com.helper
export GIT_CONFIG_VALUE_1='!f() { test "$1" = get || exit 0; echo username=x-access-token; printf "password=%s\n" "$(tr -d "[:space:]" <"$DXB_TOKEN_FILE")"; }; f'
git clone --depth 1 --filter=blob:none --sparse https://github.com/mohdeltayer/dxb-assets.git ~/dxb-assets
cd ~/dxb-assets && git sparse-checkout set ops/backoffice && ops/backoffice/backup/install.sh
EOT
```

`install.sh` copies the four units to `~/.config/systemd/user/`, runs `systemctl --user
daemon-reload`, enables both timers and creates `~/mirror/{git,snapshots,state}`. It stops with a
clear message if linger is not enabled or the two `/etc/dxb-backup` files are not readable yet.
After that the nightly run keeps the repo and the units current with `git pull`.

## First run and restore test

```
sudo -iu dxbbackup
~/dxb-assets/ops/backoffice/backup/mirror.sh status
systemctl --user start --no-block dxb-backup.service     # first mirror; dxb-assets takes hours
tail -f ~/mirror/state/backup.log
~/dxb-assets/ops/backoffice/backup/mirror.sh restore-test   # when the run has finished
```

`restore-test` clones dxb-queue from the mirror into a scratch folder, runs `git fsck --full`,
compares HEAD and every branch with the mirror, checks the latest snapshot holds the same HEAD,
prints the result and the time taken, and deletes the scratch folder. `restore-test dxb-assets`
does the same for another repo (a full clone and fsck of dxb-assets is heavy; do it off-hours).

## Modes

| Command | What |
|---|---|
| `mirror.sh nightly` | the timer's job; a no-op when tonight already succeeded |
| `mirror.sh full` | same, forced; run it after a manual full Backblaze run |
| `mirror.sh heartbeat-check` | alert if no success for 26 h (the 09:00 timer) |
| `mirror.sh restore-test [repo]` | clone, fsck, compare, time |
| `mirror.sh status` | mirrors, snapshots, last runs, free disk, timers, file readability |

Exit codes: 0 ok or nothing to do, 1 failed, 2 bad mode, 3 stopped by the disk floor, 75 skipped
because a render is active.

## Restoring from the mirror

```
git clone ~dxbbackup/mirror/git/dxb-queue.git restored-queue         # a working copy
git clone ~dxbbackup/mirror/snapshots/2026-10-27/git/dxb-queue.git x   # as of that night
git --git-dir=<mirror> push <new-empty-repo-url> 'refs/heads/*' 'refs/tags/*'   # rebuild a repo
```

Do not `push --mirror` to GitHub: the mirror holds `refs/pull/*`, which GitHub refuses. A branch that
was deleted or force-pushed on GitHub disappears from the live mirror at the next update (that is
what `--prune` does) but stays in every earlier snapshot, with its objects: nothing is ever
repacked or garbage-collected, so those files are never removed while a snapshot links them.

## Notes and limits

* The mirror and its snapshots share one disk with the server. They protect against a wrong push,
  a deleted repo or a lost GitHub account; Backblaze stays the off-server copy.
* Expected size: dxb-assets about 24 GB (20 GB history and about 4 GB of cards), dxb-queue a few
  hundred MB, dxb-fonts tiny. Snapshots add only new files, so 14 days cost little beyond the
  mirror's own growth (a few GB a month). The first run needs about 30 GB free plus the 40 GB floor.
* The render check matches on the command line, so an editor or `tail` open on a file named
  `render_job.py` also counts as a render; the run waits 30 minutes and skips.
* Never run `git gc`, `git repack` or `git prune` on the mirrors: snapshots rely on pack files never
  changing. `gc.auto` is already 0 there.
* Overrides for tests: `DXB_BACKUP_ETC`, `DXB_BACKUP_ROOT`, `DXB_BACKUP_REPOS` (`name|url|GB`,
  space separated), `DXB_BACKUP_NTFY=off`, `DXB_BACKUP_SELF_UPDATE=off`, `DXB_BACKUP_FLOOR_GB`,
  `DXB_BACKUP_BUSY_PATTERN`, `DXB_BACKUP_KEEP`, `DXB_BACKUP_WAIT_MIN`.
* Nothing here stores, prints or logs the token or topic: git reads the token from the file when it
  asks, curl gets the topic on stdin, and the log is filtered for token shapes.
