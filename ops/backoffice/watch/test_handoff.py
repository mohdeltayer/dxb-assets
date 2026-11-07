"""The public push (adv-20261107-watch-token-live): one commit, files under watch/, outlet text removed, the other
files of the branch kept. Against a local bare repository; nothing leaves the machine."""
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


class Public(unittest.TestCase):
    def test_one_commit_no_outlet_text_other_files_kept(self):
        t = tempfile.mkdtemp()
        subprocess.run(['git', 'init', '-q', '--bare', t + '/r.git'], check=True)
        open(t + '/token', 'w').write('dummy')
        h = {'remote': t + '/r.git', 'branch': 'watch-digest', 'dir': 'watch', 'token_file': t + '/token'}
        d = {'seq': 7, 'official': [{'title': 't', 'summary': 'COPIED OUTLET TEXT'}]}
        self.assertEqual(H.push_public(t + '/w', {'digest.json': json.dumps(d), 'digest.txt': 't\n'}, 'hourly', h), 'pushed')
        self.assertEqual(H.push_public(t + '/w', {'breaking.json': json.dumps({'seq': 8, 'items': []})}, 'breaking', h), 'pushed')
        self.assertEqual(git(t + '/r.git', 'log', '--format=%s', 'watch-digest').split(), ['breaking'])
        self.assertEqual(sorted(git(t + '/r.git', 'ls-tree', '-r', '--name-only', 'watch-digest').split()),
                         ['watch/breaking.json', 'watch/digest.json', 'watch/digest.txt'])
        dj = git(t + '/r.git', 'show', 'watch-digest:watch/digest.json')
        self.assertNotIn('COPIED', dj)
        self.assertEqual(json.loads(dj)['seq'], 7)

    def test_unreadable_token_pushes_nothing(self):
        with self.assertRaises(H.PushError):
            H.push_public(tempfile.mkdtemp() + '/w', {'digest.json': '{}'}, 'm',
                          {'remote': '/nonexistent', 'branch': 'b', 'token_file': '/nonexistent/token'})


if __name__ == '__main__':
    unittest.main()
