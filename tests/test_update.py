import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('updater', Path(__file__).resolve().parents[1]/'scripts/update.py')
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)


class UpdateTests(unittest.TestCase):
    def setUp(self):
        base = Path(os.environ['DPR_TEST_ROOT'])
        base.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=base)
        self.base = Path(self.tmp.name)
        self.remote = self.base/'remote.git'
        self.author = self.base/'author'
        self.client = self.base/'client'
        self.run_git('init', '--bare', str(self.remote))
        self.run_git('clone', str(self.remote), str(self.author))
        self.run_git('-C', str(self.author), 'checkout', '-b', 'main')
        self.commit(self.author, 'first')
        self.run_git('-C', str(self.author), 'push', '-u', 'origin', 'main')
        self.run_git('clone', '--branch', 'main', str(self.remote), str(self.client))

    def tearDown(self):
        self.tmp.cleanup()

    def run_git(self, *args):
        return subprocess.check_output(['git', *args], stderr=subprocess.STDOUT, text=True)

    def commit(self, repo, value):
        (repo/'data').write_text(value)
        self.run_git('-C', str(repo), 'add', 'data')
        self.run_git('-C', str(repo), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                     'commit', '-m', value)

    def test_fast_forward_and_no_change(self):
        self.commit(self.author, 'second')
        self.run_git('-C', str(self.author), 'push')
        self.assertIn('已更新到', u.update(self.client, str(self.remote)))
        self.assertEqual((self.client/'data').read_text(), 'second')
        self.assertIn('已是最新', u.update(self.client, str(self.remote)))

    def test_dirty_preserved(self):
        (self.client/'data').write_text('local')
        with self.assertRaises(RuntimeError):
            u.update(self.client, str(self.remote))
        self.assertEqual((self.client/'data').read_text(), 'local')

    def test_local_commit_preserved(self):
        self.commit(self.client, 'local commit')
        before = u.git(self.client, 'rev-parse', 'HEAD')
        with self.assertRaises(subprocess.CalledProcessError):
            u.update(self.client, str(self.remote))
        self.assertEqual(u.git(self.client, 'rev-parse', 'HEAD'), before)

    def test_wrong_origin(self):
        with self.assertRaises(RuntimeError):
            u.update(self.client)


if __name__ == '__main__':
    unittest.main()
