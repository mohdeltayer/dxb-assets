"""Hand-over to the news desk: commit the digest files to a private repo's branch and push.

The token is read by git itself from a root-owned file (a credential helper in the environment),
so it is never on a command line, in the repo, or in a log. The working clone lives under
~/backoffice/watch/handoff and is always reset to the remote tip before a commit, so losing it
costs nothing. Every `squash_days` the history is replaced by a single commit.

WATCH_PUSH=off turns the push off (tests): the files are written to the out folder only.
"""
import os
import re
import shutil
import subprocess
import time

TOKEN_RE = re.compile(r'(ghp_|github_pat_|gho_|ghs_)[A-Za-z0-9_]+')
HELPER = ('!f() { test "$1" = get || exit 0; echo username=x-access-token; '
          'printf "password=%s\\n" "$(tr -d "[:space:]" <"$WATCH_TOKEN_FILE")"; }; f')


class PushError(Exception):
    pass


def git_env(token_file):
    env = dict(os.environ)
    env.update({
        'GIT_TERMINAL_PROMPT': '0', 'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_CONFIG_NOSYSTEM': '1',
        'WATCH_TOKEN_FILE': token_file,
        'GIT_CONFIG_COUNT': '2',
        'GIT_CONFIG_KEY_0': 'credential.helper', 'GIT_CONFIG_VALUE_0': '',
        'GIT_CONFIG_KEY_1': 'credential.https://github.com.helper', 'GIT_CONFIG_VALUE_1': HELPER,
    })
    return env


def scrub(s):
    return TOKEN_RE.sub('<token>', s or '')[-400:]


def git(args, cwd, env, timeout=120, check=True):
    p = subprocess.run(['git'] + args, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    if check and p.returncode:
        raise PushError('git %s: %s' % (args[0], scrub(p.stderr or p.stdout)))
    return p


def push(workdir, files, message, h, squash_due=False):
    """Write `files` ({name: text}) into the branch and push. Returns 'pushed' or 'unchanged'.

    h: the handoff config (remote, branch, token_file, commit_name, commit_email).
    Raises PushError on any failure; the caller leaves the items pending and retries next pass.
    """
    token = h['token_file']
    if not os.access(token, os.R_OK):
        raise PushError('token file %s is missing or not readable by %s' % (token, os.environ.get('USER', 'this user')))
    env = git_env(token)
    remote, branch = h['remote'], h['branch']
    ident = ['-c', 'user.name=' + h.get('commit_name', 'dxb-watch'), '-c', 'user.email=' + h.get('commit_email', 'noreply@github.com'),
             '-c', 'commit.gpgsign=false']
    os.makedirs(workdir, exist_ok=True)
    if not os.path.isdir(os.path.join(workdir, '.git')):
        git(['init', '-q'], workdir, env)
    git(['remote', 'remove', 'origin'], workdir, env, check=False)
    git(['remote', 'add', 'origin', remote], workdir, env)
    fetched = git(['fetch', '-q', '--depth', '1', '--no-tags', 'origin', branch], workdir, env, check=False)
    if fetched.returncode == 0:
        git(['checkout', '-q', '-B', 'work', 'FETCH_HEAD'], workdir, env)
        git(['reset', '-q', '--hard', 'FETCH_HEAD'], workdir, env)
    elif 'couldn' in (fetched.stderr or '') and 'find remote ref' in (fetched.stderr or ''):
        git(['checkout', '-q', '--orphan', 'work'], workdir, env, check=False)   # first push: the branch does not exist yet
        git(['rm', '-rq', '--cached', '.'], workdir, env, check=False)
        squash_due = False
    else:
        raise PushError('fetch: ' + scrub(fetched.stderr))
    for name, text in files.items():
        with open(os.path.join(workdir, name), 'w', encoding='utf-8') as f:
            f.write(text)
    git(['add', '-A'], workdir, env)
    if git(['diff', '--cached', '--quiet'], workdir, env, check=False).returncode == 0 and not squash_due:
        return 'unchanged'
    if squash_due:
        git(['checkout', '-q', '--orphan', 'squashed'], workdir, env)
        git(['add', '-A'], workdir, env)
        git(ident + ['commit', '-q', '-m', message + ' [history squashed]'], workdir, env)
        git(['push', '-q', '--force', 'origin', 'squashed:refs/heads/' + branch], workdir, env)
        git(['branch', '-q', '-D', 'work'], workdir, env, check=False)
        git(['branch', '-q', '-m', 'work'], workdir, env, check=False)
        return 'pushed'
    git(ident + ['commit', '-q', '-m', message], workdir, env)
    for attempt, wait in enumerate((0, 2, 4)):
        time.sleep(wait)
        p = git(['push', '-q', 'origin', 'HEAD:refs/heads/' + branch], workdir, env, check=False)
        if p.returncode == 0:
            return 'pushed'
        err = p.stderr or ''
        if 'non-fast-forward' in err or 'rejected' in err or 'fetch first' in err:
            raise PushError('push rejected (remote moved): next pass starts again from the remote tip')
    raise PushError('push: ' + scrub(err))


def strip_public(name, text):
    """The public copy (dxb-assets is public): a JSON file loses every `summary` (the copied outlet text); the text
    files carry titles, links and times only and go as they are."""
    if not name.endswith('.json'):
        return text
    import json

    def strip(x):
        if isinstance(x, dict):
            return {k: strip(v) for k, v in x.items() if k != 'summary'}
        if isinstance(x, list):
            return [strip(v) for v in x]
        return x
    return json.dumps(strip(json.loads(text)), ensure_ascii=False, indent=1)


KEEP_DIGESTS = 48            # adv-20261107-watch-token-live addendum_0700: the last 48 hourly digests stay as files


def digest_seq(text):
    import json
    try:
        return int(json.loads(text).get('seq'))
    except (ValueError, TypeError, AttributeError):
        return None


def prune_digests(folder, keep=KEEP_DIGESTS):
    """Keep the `keep` newest <seq>.json files in folder (by seq number); returns the names removed."""
    if not os.path.isdir(folder):
        return []
    seqs = sorted((int(n[:-5]), n) for n in os.listdir(folder) if n.endswith('.json') and n[:-5].isdigit())
    gone = [n for _, n in seqs[:-keep]] if len(seqs) > keep else []
    for n in gone:
        os.remove(os.path.join(folder, n))
    return gone


def push_public(workdir, files, message, h, keep=KEEP_DIGESTS, attempts=3):
    """The public branch of dxb-assets (adv-20261107-watch-token-live): the files go under h['dir'] (watch/) with the
    outlet text removed, the other files of the branch are kept. Since 9 Nov (addendum_0700) every hourly digest is
    also kept as watch/digests/<seq>.json, the newest `keep` of them, and the commit goes on top of the branch tip and
    is pushed without force, so a reader's plain fetch always moves and no digest is lost between two reads. A
    rejected push (the branch moved: the fallback workflow or another pass) re-fetches and tries again, `attempts`
    times in all. Returns 'pushed' or 'unchanged'. Raises PushError; the caller leaves the items pending."""
    token = h['token_file']
    if not os.access(token, os.R_OK):
        raise PushError('token file %s is missing or not readable by %s' % (token, os.environ.get('USER', 'this user')))
    env = git_env(token)
    remote, branch, sub = h['remote'], h['branch'], h.get('dir') or 'watch'
    ident = ['-c', 'user.name=' + h.get('commit_name', 'dxb-watch'), '-c', 'user.email=' + h.get('commit_email', 'noreply@github.com'),
             '-c', 'commit.gpgsign=false']
    err = ''
    for attempt in range(attempts):
        if attempt:
            time.sleep(2 * attempt)
        shutil.rmtree(workdir, ignore_errors=True)
        os.makedirs(workdir)
        git(['init', '-q'], workdir, env)
        git(['remote', 'add', 'origin', remote], workdir, env)
        fetched = git(['fetch', '-q', '--depth', '1', '--no-tags', 'origin', branch], workdir, env, check=False)
        if fetched.returncode == 0:
            git(['checkout', '-q', '-B', 'work', 'FETCH_HEAD'], workdir, env)
        elif 'find remote ref' in (fetched.stderr or ''):
            git(['checkout', '-q', '--orphan', 'work'], workdir, env)
        else:
            raise PushError('fetch: ' + scrub(fetched.stderr))
        os.makedirs(os.path.join(workdir, sub), exist_ok=True)
        for name, text in files.items():
            public = strip_public(name, text)
            with open(os.path.join(workdir, sub, name), 'w', encoding='utf-8') as f:
                f.write(public)
            if name == 'digest.json':
                seq = digest_seq(public)
                if seq is not None:
                    os.makedirs(os.path.join(workdir, sub, 'digests'), exist_ok=True)
                    with open(os.path.join(workdir, sub, 'digests', '%d.json' % seq), 'w', encoding='utf-8') as f:
                        f.write(public)
        prune_digests(os.path.join(workdir, sub, 'digests'), keep)
        git(['add', '-A'], workdir, env)
        if git(['diff', '--cached', '--quiet'], workdir, env, check=False).returncode == 0:
            return 'unchanged'
        git(ident + ['commit', '-q', '-m', message], workdir, env)
        p = git(['push', '-q', 'origin', 'HEAD:refs/heads/' + branch], workdir, env, check=False)
        if p.returncode == 0:
            return 'pushed'
        err = p.stderr or ''
        if not ('rejected' in err or 'non-fast-forward' in err or 'fetch first' in err or 'stale info' in err):
            break
    raise PushError('push: ' + scrub(err))


def reset(workdir):
    shutil.rmtree(workdir, ignore_errors=True)
