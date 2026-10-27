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


def reset(workdir):
    shutil.rmtree(workdir, ignore_errors=True)
