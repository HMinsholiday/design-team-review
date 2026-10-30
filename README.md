# 设计团队内部 AI 预评审

评审页面框架、视觉一致性、组件一致性、交互合理性与体验优化空间。在 Figma 原稿外添加编号、引线和精简说明卡片，所有标注归入一个父图层，可整体隐藏或删除。原稿不改动，不使用原生评论。

## 同事安装（macOS）

先准备 Git、Python 3 和 Codex。Figma 插件需各自安装、登录并取得目标设计文件访问权限；本仓库不共享账号和授权。

在终端执行：

```bash
mkdir -p "$HOME/Library/Mobile Documents/com~apple~CloudDocs/🧬chatGPT/新项目"
git clone https://github.com/HMinsholiday/-.git "$HOME/Library/Mobile Documents/com~apple~CloudDocs/🧬chatGPT/新项目/设计团队内部AI预评共享"
python3 "$HOME/Library/Mobile Documents/com~apple~CloudDocs/🧬chatGPT/新项目/设计团队内部AI预评共享/scripts/install.py"
```

也可以把本仓库链接发给 Codex，说：“请阅读 README，为我安装此 skill 并启用自动更新。”安装会启用每 5 分钟一次的本机后台检查。只下载源文件不会自动启用更新。

安装脚本不覆盖已有同名技能；遇到旧入口或独立副本时，先确认其内容，再迁移，避免同名 skill 被重复发现。安装成功后使用 `$design-pre-review`；未出现时重启 Codex。

## 更新方式

维护者更新 `design-pre-review/`，提交并推送 `main`。同事电脑开机、登录且联网时，通常在 5 分钟左右拉取新版；不是秒级推送。休眠、离线或 GitHub 访问失败时等下次检查。Codex 若未发现更新，请重启；已开始的评审不保证中途切换版本。

自动更新只接受指定仓库 `main` 的快进更新。有本地修改、未跟踪文件、本地提交、错误分支或分叉时停止，不 reset、不 stash、不覆盖。同事建议只使用技能，通过反馈或 PR 提议修改。

技能内容位于 iCloud 的仓库目录；本机运行状态、锁文件和日志位于 `~/.codex/design-pre-review-sync/`，LaunchAgent 位于 `~/Library/LaunchAgents/com.designteam.design-pre-review-sync.plist`，不把这些机器状态用于双机共享。

更新器使用安装时复制到本机的固定脚本。若维护者更新安装器或更新程序，需重新运行 `scripts/install.py` 升级本机运行程序；skill 本身继续自动更新。

## 手动更新与排查

```bash
python3 "$HOME/Library/Mobile Documents/com~apple~CloudDocs/🧬chatGPT/新项目/设计团队内部AI预评共享/scripts/update.py" --repo "$HOME/Library/Mobile Documents/com~apple~CloudDocs/🧬chatGPT/新项目/设计团队内部AI预评共享"
tail -n 20 "$HOME/.codex/design-pre-review-sync/update.log"
```

日志显示失败时先处理原因，不要强制重置仓库。更新需要 Git 可用且无需交互登录；当前公开仓库正常情况下无需 GitHub 登录。

暂停自动更新：

```bash
launchctl bootout "gui/$(id -u)/com.designteam.design-pre-review-sync"
```

再次运行安装器可恢复。彻底停用时，移走对应 LaunchAgent plist，避免下次登录重新启用；移除 skill 软链接不会删除仓库。Windows/Linux 可克隆仓库后配置各自技能目录和系统调度，本安装器仅提供 macOS 自动更新；可使用 `--no-auto-update --repo-dir 路径 --skills-dir 路径` 仅安装软链接。

## 使用

向 Codex 发送 Figma 链接并说：

> 用 $design-pre-review 评审这个页面，在独立图层里标注问题。文案简短，使用带底色的 P0/P1/P2/P3 标签，不改原稿。

每次评审报告记录本次 skill 的 Git 提交版本，便于复核。工具没有读取本地 Git 的能力时标记“版本未知”，不编造版本号。

## 本地验证

在仓库根目录运行以下命令；测试文件位于指定 iCloud 临时工作目录，并在测试结束清理：

```bash
DPR_TEST_ROOT="$HOME/Library/Mobile Documents/com~apple~CloudDocs/🧬chatGPT/临时工作/skill-sync-tests" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```
