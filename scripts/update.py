#!/usr/bin/env python3
"""Fast-forward a read-only skill checkout; never discard local work."""
import argparse
import fcntl
import os
from pathlib import Path
import subprocess

ORIGIN = 'https://github.com/HMinsholiday/-.git'


def git(repo, *args):
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GIT_SSH_COMMAND='ssh -o BatchMode=yes')
    return subprocess.check_output(['git', '-C', str(repo), *args], env=env,
                                   stderr=subprocess.STDOUT, timeout=60, text=True).strip()


def update(repo, expected_origin=ORIGIN):
    repo = Path(repo).resolve()
    if git(repo, 'remote', 'get-url', 'origin') != expected_origin:
        raise RuntimeError('origin 不匹配，已停止更新')
    if git(repo, 'symbolic-ref', '--short', 'HEAD') != 'main':
        raise RuntimeError('当前不在 main 分支，已停止更新')
    if git(repo, 'status', '--porcelain', '--untracked-files=all'):
        raise RuntimeError('存在本地修改或未跟踪文件，已停止更新')
    before = git(repo, 'rev-parse', 'HEAD')
    git(repo, 'fetch', '--no-tags', 'origin', 'refs/heads/main')
    target = git(repo, 'rev-parse', 'FETCH_HEAD')
    # Reject both divergent history and unpublished local commits.
    git(repo, 'merge-base', '--is-ancestor', before, target)
    if git(repo, 'status', '--porcelain', '--untracked-files=all'):
        raise RuntimeError('拉取期间出现本地修改，已停止更新')
    git(repo, '-c', 'core.hooksPath=/dev/null', 'merge', '--ff-only', target)
    return ('已是最新版本 ' if before == target else '已更新到 ') + target[:12]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--state-dir', type=Path,
                        default=Path.home()/'.codex/design-pre-review-sync')
    args = parser.parse_args()
    args.state_dir.mkdir(parents=True, exist_ok=True)
    with (args.state_dir/'update.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        try:
            print(update(args.repo), flush=True)
        except (RuntimeError, subprocess.SubprocessError, OSError) as exc:
            print('更新未完成：' + str(exc), flush=True)
            raise SystemExit(1)


if __name__ == '__main__':
    main()
