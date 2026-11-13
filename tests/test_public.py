import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

spec = importlib.util.spec_from_file_location('public_check', Path(__file__).resolve().parents[1] / 'scripts/check_public.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class PublicCheckTests(unittest.TestCase):
    def test_anonymous_access_passes(self):
        metadata = json.dumps({'private': False, 'full_name': p.REPOSITORY, 'default_branch': 'main'}).encode()
        with patch.object(p, 'fetch', side_effect=[metadata] + [b'file'] * 5 + [b'git-upload-pack refs/heads/main']) as fetch:
            p.check()
            self.assertEqual(fetch.call_count, 7)

    def test_private_repository_stops_distribution(self):
        metadata = json.dumps({'private': True, 'full_name': p.REPOSITORY, 'default_branch': 'main'}).encode()
        with patch.object(p, 'fetch', return_value=metadata) as fetch:
            with self.assertRaisesRegex(RuntimeError, '未公开'):
                p.check()
            self.assertEqual(fetch.call_count, 1)

    def test_404_has_actionable_message_and_nonzero_exit(self):
        error = HTTPError('https://example.invalid', 404, 'Not Found', {}, None)
        with patch.object(p, 'fetch', side_effect=error), patch('sys.stderr') as stderr:
            self.assertEqual(p.main(), 1)
            self.assertIn('可见性', ''.join(call.args[0] for call in stderr.write.call_args_list))

    def test_git_endpoint_without_main_fails(self):
        metadata = json.dumps({'private': False, 'full_name': p.REPOSITORY, 'default_branch': 'main'}).encode()
        with patch.object(p, 'fetch', side_effect=[metadata] + [b'file'] * 5 + [b'login page']):
            with self.assertRaisesRegex(RuntimeError, 'main 失败'):
                p.check()
