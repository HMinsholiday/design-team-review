#!/usr/bin/env python3
"""Verify public installation access without GitHub credentials or browser cache."""
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPOSITORY = 'HMinsholiday/design-team-review'


def fetch(url):
    request = Request(url, headers={'User-Agent': 'design-team-review-public-check',
                                   'Cache-Control': 'no-cache'})
    with urlopen(request, timeout=30) as response:
        return response.read()


def check():
    metadata = json.loads(fetch('https://api.github.com/repos/' + REPOSITORY))
    if metadata.get('private') is not False or metadata.get('full_name') != REPOSITORY:
        raise RuntimeError('仓库未公开，或仓库地址已变化')
    if metadata.get('default_branch') != 'main':
        raise RuntimeError('默认分支不是 main，请同步安装与更新配置')
    for path in ('README.md', 'design-team-review/SKILL.md', 'scripts/install.py',
                 'scripts/update.py', 'sync-config.json'):
        if not fetch('https://raw.githubusercontent.com/' + REPOSITORY + '/main/' + path):
            raise RuntimeError('远端文件为空：' + path)
        print('匿名读取通过：' + path)
    refs = fetch('https://github.com/' + REPOSITORY + '.git/info/refs?service=git-upload-pack')
    if b'refs/heads/main' not in refs or b'git-upload-pack' not in refs:
        raise RuntimeError('Git 匿名读取 main 失败')
    print('通过：公开仓库、安装文件及 Git main 均可匿名读取；无需 GitHub 登录。')


def main():
    try:
        check()
    except HTTPError as exc:
        if exc.code == 404:
            print('检查失败：匿名访问返回 404，可能是私有、改名、转移或删除。'
                  '请维护者检查仓库可见性和地址，修复前不要分发安装通知。', file=sys.stderr)
        else:
            print('检查失败：HTTP ' + str(exc.code) + '；请排查网络或 GitHub 限流。', file=sys.stderr)
        return 1
    except (URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
        print('检查失败：' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
