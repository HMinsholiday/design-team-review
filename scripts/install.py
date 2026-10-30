#!/usr/bin/env python3
"""Install the skill symlink and optional macOS five-minute updater."""
import argparse
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
from update import ORIGIN, git, update

LABEL = 'com.designteam.design-pre-review-sync'


def main():
    home = Path.home()
    root = home/'Library/Mobile Documents/com~apple~CloudDocs/🧬chatGPT'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-dir', type=Path, default=root/'新项目/设计团队内部AI预评共享')
    parser.add_argument('--skills-dir', type=Path, default=home/'.agents/skills')
    parser.add_argument('--no-auto-update', action='store_true')
    args = parser.parse_args()
    if sys.platform != 'darwin' and not args.no_auto_update:
        parser.error('自动更新安装仅支持 macOS；其他系统请加 --no-auto-update')
    repo = args.repo_dir.expanduser().resolve()
    link = args.skills_dir.expanduser().absolute()/'design-pre-review'
    target = repo/'design-pre-review'
    if os.path.lexists(link) and (not link.is_symlink() or link.resolve() != target):
        parser.error('已有同名技能，未覆盖：' + str(link))
    # Prevent duplicate discovery through the older Codex location.
    legacy = home/'.codex/skills/design-pre-review'
    if legacy != link and os.path.lexists(legacy):
        parser.error('发现旧安装入口，请先确认并迁移，未覆盖：' + str(legacy))
    if repo.exists():
        print(update(repo))
    else:
        repo.parent.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, GIT_TERMINAL_PROMPT='0')
        subprocess.run(['git', 'clone', '--branch', 'main', '--single-branch', ORIGIN, str(repo)],
                       check=True, env=env, timeout=120)
    if not (target/'SKILL.md').is_file():
        raise RuntimeError('未找到 SKILL.md')
    link.parent.mkdir(parents=True, exist_ok=True)
    if not link.is_symlink():
        link.symlink_to(target, target_is_directory=True)
    if not args.no_auto_update:
        state = home/'.codex/design-pre-review-sync'
        state.mkdir(parents=True, exist_ok=True)
        # Fixed machine-local launcher survives checkout updates.
        runner = state/'update.py'
        shutil.copy2(repo/'scripts/update.py', runner)
        plist = home/'Library/LaunchAgents'/f'{LABEL}.plist'
        plist.parent.mkdir(parents=True, exist_ok=True)
        python = str(Path(sys.executable).resolve())
        data = {'Label': LABEL, 'ProgramArguments': [python, str(runner), '--repo', str(repo),
                '--state-dir', str(state)], 'RunAtLoad': True, 'StartInterval': 300,
                'StandardOutPath': str(state/'update.log'), 'StandardErrorPath': str(state/'update.log')}
        plist.write_bytes(plistlib.dumps(data))
        domain = f'gui/{os.getuid()}'
        subprocess.run(['launchctl', 'bootout', domain+'/'+LABEL], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        subprocess.run(['launchctl', 'bootstrap', domain, str(plist)], check=True)
        print('自动更新已启用：每 5 分钟检查一次，登录后补查。')
    print('安装完成：' + str(link))
    print('版本：' + git(repo, 'rev-parse', '--short', 'HEAD'))
    print('使用 $design-pre-review；未显示时重启 Codex。')


if __name__ == '__main__':
    main()
