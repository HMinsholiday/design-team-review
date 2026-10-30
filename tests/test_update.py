import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import json
from unittest.mock import patch

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

    def test_legacy_origin_migration(self):
        renamed = self.base/'renamed.git'
        renamed.symlink_to(self.remote, target_is_directory=True)
        previous = u.ORIGIN, u.LEGACY_ORIGIN
        try:
            u.ORIGIN, u.LEGACY_ORIGIN = str(renamed), str(self.remote)
            self.assertIn('已是最新', u.update(self.client, str(renamed)))
            self.assertEqual(u.git(self.client, 'remote', 'get-url', 'origin'), str(renamed))
        finally:
            u.ORIGIN, u.LEGACY_ORIGIN = previous

    def test_wrong_origin(self):
        with self.assertRaises(RuntimeError):
            u.update(self.client)


class ScheduleTests(unittest.TestCase):
    def test_new_interval_applies_after_sync_and_not_before_due(self):
        base = Path(os.environ['DPR_TEST_ROOT'])
        with tempfile.TemporaryDirectory(dir=base) as d:
            repo = Path(d)
            config = repo/'sync-config.json'
            config.write_text(json.dumps({'check_interval_seconds': 86400}))
            def sync(*args):
                config.write_text(json.dumps({'check_interval_seconds': 3600}))
                return 'updated'
            with patch.object(u, 'update', side_effect=sync) as mocked:
                u.scheduled_update(repo, repo, now=100)
                self.assertEqual(json.loads((repo/'schedule.json').read_text())['next_check_at'], 3700)
                self.assertIsNone(u.scheduled_update(repo, repo, now=3699))
                self.assertEqual(mocked.call_count, 1)
                u.scheduled_update(repo, repo, now=3700)
                self.assertEqual(mocked.call_count, 2)

    def test_invalid_config_never_calls_network(self):
        base = Path(os.environ['DPR_TEST_ROOT'])
        with tempfile.TemporaryDirectory(dir=base) as d:
            repo = Path(d)
            for value in [True, 0, '3600', 2592001]:
                (repo/'sync-config.json').write_text(json.dumps({'check_interval_seconds': value}))
                with patch.object(u, 'update') as mocked:
                    with self.assertRaises(RuntimeError):
                        u.scheduled_update(repo, repo, now=100)
                    mocked.assert_not_called()

    def test_failure_does_not_retry_each_minute(self):
        base = Path(os.environ['DPR_TEST_ROOT'])
        with tempfile.TemporaryDirectory(dir=base) as d:
            repo = Path(d)
            (repo/'sync-config.json').write_text(json.dumps({'check_interval_seconds': 86400}))
            with patch.object(u, 'update', side_effect=OSError('offline')) as mocked:
                with self.assertRaises(OSError):
                    u.scheduled_update(repo, repo, now=100)
                self.assertIsNone(u.scheduled_update(repo, repo, now=160))
                self.assertEqual(mocked.call_count, 1)


if __name__ == '__main__':
    unittest.main()
