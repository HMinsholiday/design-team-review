#!/usr/bin/env python3
"""Fast-forward a read-only skill checkout; never discard local work."""
import argparse
import fcntl
import os
import json
import time
from pathlib import Path
import subprocess

ORIGIN = 'https://github.com/HMinsholiday/design-team-review.git'
LEGACY_ORIGIN = 'https://github.com/HMinsholiday/-.git'


def git(repo, *args):
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GIT_SSH_COMMAND='ssh -o BatchMode=yes')
    return subprocess.check_output(['git', '-C', str(repo), *args], env=env,
                                   stderr=subprocess.STDOUT, timeout=60, text=True).strip()


def update(repo, expected_origin=ORIGIN):
    repo = Path(repo).resolve()
    actual_origin = git(repo, 'remote', 'get-url', 'origin')
    legacy = expected_origin == ORIGIN and actual_origin == LEGACY_ORIGIN
    if actual_origin != expected_origin and not legacy:
        raise RuntimeError('origin 不匹配，已停止更新')
    if git(repo, 'symbolic-ref', '--short', 'HEAD') != 'main':
        raise RuntimeError('当前不在 main 分支，已停止更新')
    if git(repo, 'status', '--porcelain', '--untracked-files=all'):
        raise RuntimeError('存在本地修改或未跟踪文件，已停止更新')
    before = git(repo, 'rev-parse', 'HEAD')
    git(repo, 'fetch', '--no-tags', expected_origin, 'refs/heads/main')
    target = git(repo, 'rev-parse', 'FETCH_HEAD')
    # Reject both divergent history and unpublished local commits.
    git(repo, 'merge-base', '--is-ancestor', before, target)
    if git(repo, 'status', '--porcelain', '--untracked-files=all'):
        raise RuntimeError('拉取期间出现本地修改，已停止更新')
    git(repo, '-c', 'core.hooksPath=/dev/null', 'merge', '--ff-only', target)
    if legacy:
        git(repo, 'remote', 'set-url', 'origin', ORIGIN)
    return ('已是最新版本 ' if before == target else '已更新到 ') + target[:12]


def read_interval(repo):
    value = json.loads((Path(repo)/'sync-config.json').read_text()).get('check_interval_seconds')
    if type(value) is not int or not 60 <= value <= 2592000:
        raise RuntimeError('check_interval_seconds 必须是 60 到 2592000 的整数')
    return value


def scheduled_update(repo, state_dir, expected_origin=ORIGIN, now=None):
    now = time.time() if now is None else now
    state_file = Path(state_dir)/'schedule.json'
    interval = read_interval(repo)
    state = json.loads(state_file.read_text()) if state_file.exists() else {}
    if now < state.get('next_check_at', 0):
        return None
    # Record attempt before network access to avoid retrying every local tick offline.
    state_file.write_text(json.dumps({'next_check_at': now + interval}))
    result = update(repo, expected_origin)
    interval = read_interval(repo)  # Newly downloaded team configuration.
    state_file.write_text(json.dumps({'next_check_at': now + interval}))
    return result + '；下次检查间隔 ' + str(interval) + ' 秒'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--state-dir', type=Path,
                        default=Path.home()/'.codex/design-pre-review-sync')
    parser.add_argument('--scheduled', action='store_true')
    args = parser.parse_args()
    args.state_dir.mkdir(parents=True, exist_ok=True)
    with (args.state_dir/'update.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        try:
            result = scheduled_update(args.repo, args.state_dir) if args.scheduled else update(args.repo)
            if result:
                print(result, flush=True)
        except (RuntimeError, ValueError, subprocess.SubprocessError, OSError) as exc:
            print('更新未完成：' + str(exc), flush=True)
            raise SystemExit(1)


if __name__ == '__main__':
    main()
