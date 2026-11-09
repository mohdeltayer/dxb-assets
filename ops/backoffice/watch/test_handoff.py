"""The public push (adv-20261107-watch-token-live, addendum_0700 of 9 Nov): files under watch/, outlet text removed, the
other files of the branch kept, each hourly digest also kept as watch/digests/<seq>.json (newest 48), commits on top of
the branch tip with no force, a rejected push retried from a fresh fetch. Against a local bare repository; nothing
leaves the machine."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import handoff as H  # noqa: E402


def git(d, *a):
    return subprocess.run(['git', '--git-dir', d] + list(a), capture_output=True, text=True).stdout


def setup():
    t = tempfile.mkdtemp()
    subprocess.run(['git', 'init', '-q', '--bare', t + '/r.git'], check=True)
    with open(t + '/token', 'w') as f:
        f.write('dummy')
    h = {'remote': t + '/r.git', 'branch': 'watch-digest', 'dir': 'watch', 'token_file': t + '/token'}
    return t, h


def digest(seq, text='t'):
    return {'digest.json': json.dumps({'seq': seq, 'official': [{'title': text, 'summary': 'COPIED OUTLET TEXT'}]}),
            'digest.txt': text + '\n'}


def other_commit(t, name, msg):
    """Someone else (the fallback workflow) commits to the branch."""
    w = tempfile.mkdtemp()
    env = dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null')
    subprocess.run(['git', 'clone', '-q', '--branch', 'watch-digest', t + '/r.git', w], check=True, env=env)
    with open(os.path.join(w, name), 'w') as f:
        f.write(msg)
    subprocess.run(['git', '-C', w, 'add', '-A'], check=True, env=env)
    subprocess.run(['git', '-C', w, '-c', 'user.name=x', '-c', 'user.email=x@x', 'commit', '-q', '-m', msg], check=True, env=env)
    subprocess.run(['git', '-C', w, 'push', '-q', 'origin', 'HEAD:refs/heads/watch-digest'], check=True, env=env)


class Public(unittest.TestCase):
    def test_history_kept_no_force_digest_files_no_outlet_text(self):
        t, h = setup()
        self.assertEqual(H.push_public(t + '/w', digest(7), 'hourly 7', h), 'pushed')
        self.assertEqual(H.push_public(t + '/w', {'breaking.json': json.dumps({'seq': 8, 'items': []})}, 'breaking 8', h), 'pushed')
        other_commit(t, 'watch/note.txt', 'fallback commit')
        self.assertEqual(H.push_public(t + '/w', digest(9), 'hourly 9', h), 'pushed')
        self.assertEqual(git(t + '/r.git', 'log', '--format=%s', 'watch-digest').splitlines(),
                         ['hourly 9', 'fallback commit', 'breaking 8', 'hourly 7'])
        self.assertEqual(sorted(git(t + '/r.git', 'ls-tree', '-r', '--name-only', 'watch-digest').split()),
                         ['watch/breaking.json', 'watch/digest.json', 'watch/digest.txt', 'watch/digests/7.json',
                          'watch/digests/9.json', 'watch/note.txt'])
        for f in ('watch/digest.json', 'watch/digests/7.json', 'watch/digests/9.json'):
            self.assertNotIn('COPIED', git(t + '/r.git', 'show', 'watch-digest:' + f))
        self.assertEqual(json.loads(git(t + '/r.git', 'show', 'watch-digest:watch/digest.json'))['seq'], 9)
        self.assertEqual(json.loads(git(t + '/r.git', 'show', 'watch-digest:watch/digests/7.json'))['seq'], 7)

    def test_only_the_newest_digests_are_kept(self):
        t, h = setup()
        for seq in (1, 2, 3, 10, 11):
            H.push_public(t + '/w', digest(seq, 's%d' % seq), 'hourly %d' % seq, h, keep=3)
        names = git(t + '/r.git', 'ls-tree', '--name-only', 'watch-digest:watch/digests').split()
        self.assertEqual(sorted(names), ['10.json', '11.json', '3.json'])
        self.assertEqual(H.KEEP_DIGESTS, 48)

    def test_same_files_again_is_unchanged(self):
        t, h = setup()
        H.push_public(t + '/w', digest(4), 'hourly 4', h)
        self.assertEqual(H.push_public(t + '/w', digest(4), 'hourly 4 again', h), 'unchanged')

    def test_rejected_push_refetches_and_lands_on_top(self):
        t, h = setup()
        H.push_public(t + '/w', digest(20), 'hourly 20', h)
        real, state = H.git, {'n': 0}

        def racing(args, cwd, env, timeout=120, check=True):
            if args[0] == 'push' and state['n'] == 0:      # the branch moves between our fetch and our push
                state['n'] += 1
                other_commit(t, 'watch/race.txt', 'raced in')
            return real(args, cwd, env, timeout, check)
        H.git = racing
        try:
            self.assertEqual(H.push_public(t + '/w', digest(21), 'hourly 21', h), 'pushed')
        finally:
            H.git = real
        self.assertEqual(git(t + '/r.git', 'log', '--format=%s', 'watch-digest').splitlines(),
                         ['hourly 21', 'raced in', 'hourly 20'])

    def test_first_push_creates_the_branch(self):
        t, h = setup()
        self.assertEqual(H.push_public(t + '/w', digest(1), 'first', h), 'pushed')
        self.assertIn('watch/digests/1.json', git(t + '/r.git', 'ls-tree', '-r', '--name-only', 'watch-digest'))

    def test_unreadable_token_pushes_nothing(self):
        with self.assertRaises(H.PushError):
            H.push_public(tempfile.mkdtemp() + '/w', {'digest.json': '{}'}, 'm',
                          {'remote': '/nonexistent', 'branch': 'b', 'token_file': '/nonexistent/token'})


class SelfUpdate(unittest.TestCase):
    """The server's stable clone is shallow and the keeper moves origin/main with --depth 1, so a pull cannot
    fast-forward; self_update fetches and resets --keep instead (9 Nov)."""
    def test_shallow_clone_moved_by_a_depth_1_fetch_still_updates(self):
        try:
            import watch as W
        except ImportError as e:                       # PyYAML missing on this machine
            self.skipTest(str(e))
        t = tempfile.mkdtemp()
        env = dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null')
        g = lambda *a, **k: subprocess.run(['git'] + list(a), check=True, env=env, capture_output=True, text=True, **k)
        g('init', '-q', '--bare', '-b', 'main', t + '/r.git')
        g('clone', '-q', t + '/r.git', t + '/dev')
        def commit(msg):
            with open(t + '/dev/f.txt', 'a') as f:
                f.write(msg + '\n')
            g('-C', t + '/dev', 'add', '-A')
            g('-C', t + '/dev', '-c', 'user.name=x', '-c', 'user.email=x@x', 'commit', '-q', '-m', msg)
            g('-C', t + '/dev', 'push', '-q', 'origin', 'HEAD:refs/heads/main')
        commit('one')
        commit('two')
        g('clone', '-q', '--depth', '1', '--branch', 'main', 'file://' + t + '/r.git', t + '/stable')
        commit('three')
        commit('four')
        g('-C', t + '/stable', 'fetch', '-q', '--depth', '1', 'origin', '+refs/heads/main:refs/remotes/origin/main')
        pull = subprocess.run(['git', '-C', t + '/stable', 'pull', '--ff-only', '-q'], env=env, capture_output=True, text=True)
        real = W.handoff_repo
        W.handoff_repo = lambda: t + '/stable'
        os.environ.pop('WATCH_SELF_UPDATE', None)
        try:
            W.self_update()
        finally:
            W.handoff_repo = real
        head = g('-C', t + '/stable', 'log', '-1', '--format=%s').stdout.strip()
        self.assertEqual(head, 'four', 'pull said: %s' % pull.stderr.strip())
        with open(t + '/stable/f.txt', 'a') as f:      # local changes: left alone
            f.write('local\n')
        commit('five')
        W.handoff_repo = lambda: t + '/stable'
        try:
            W.self_update()
        finally:
            W.handoff_repo = real
        self.assertEqual(g('-C', t + '/stable', 'log', '-1', '--format=%s').stdout.strip(), 'four')


if __name__ == '__main__':
    unittest.main()
