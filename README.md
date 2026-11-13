# 设计团队内部 AI 预评审

评审页面框架、视觉一致性、组件一致性、交互合理性与体验优化空间。在 Figma 原稿外添加编号、引线和精简说明卡片，所有标注归入一个父图层，可整体隐藏或删除。原稿不改动，不使用原生评论。

## 同事安装（macOS）

本分发流程要求仓库保持 **Public（公开）**，同事无需 GitHub 账号或仓库成员权限。改为私有会使匿名读取 README、安装和自动更新失败；公开后任何人都可读取已发布文件及 Git 历史，勿提交内部资料或凭据。

维护者每次分发安装通知前，运行以下命令做匿名访问检查（不依赖浏览器登录或网页搜索缓存）：

```bash
python3 scripts/check_public.py
```

仅在检查通过后发送安装链接。若同事仍收到 404，先在无痕窗口确认链接，再让维护者检查仓库可见性及地址；404 本身不能证明仓库已删除。检查不会修改仓库或系统配置。

先准备 Git、Python 3 和 Codex。Figma 插件需各自安装、登录并取得目标设计文件访问权限；本仓库不共享账号和授权。

在终端执行：

```bash
mkdir -p "$HOME/Library/Mobile Documents/com~apple~CloudDocs/🧬chatGPT/新项目"
git clone https://github.com/HMinsholiday/design-team-review.git "$HOME/Library/Mobile Documents/com~apple~CloudDocs/🧬chatGPT/新项目/设计团队内部AI预评共享"
python3 "$HOME/Library/Mobile Documents/com~apple~CloudDocs/🧬chatGPT/新项目/设计团队内部AI预评共享/scripts/install.py"
```

也可以把本仓库链接发给 Codex，说：“请阅读 README，为我安装此 skill 并启用自动更新。”安装会启用每小时一次的远端检查。只下载源文件不会自动启用更新。

安装脚本不覆盖已有同名技能；遇到旧入口或独立副本时，先确认其内容，再迁移，避免同名 skill 被重复发现。安装成功后使用 `$design-team-review`；未出现时重启 Codex。

## 更新方式

维护者更新 `design-team-review/`，提交并推送 `main`。同事电脑开机、登录且联网时，按每小时一次的频率检查并拉取新版，到期后登录时补查；不是实时推送。休眠、离线或 GitHub 访问失败时等下次检查。Codex 若未发现更新，请重启；已开始的评审不保证中途切换版本。

自动更新只接受指定仓库 `main` 的快进更新。有本地修改、未跟踪文件、本地提交、错误分支或分叉时停止，不 reset、不 stash、不覆盖。同事建议只使用技能，通过反馈或 PR 提议修改。

技能内容位于 iCloud 的仓库目录；本机运行状态、锁文件和日志位于 `~/.codex/design-pre-review-sync/`，LaunchAgent 位于 `~/Library/LaunchAgents/com.designteam.design-pre-review-sync.plist`，不把这些机器状态用于双机共享。

新版安装器使用固定本机启动入口加载仓库内的更新程序。技能、更新程序及检查周期配置均随 Git 发布；修改安装路径或后台服务结构时仍需重新运行安装器。

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

> 用 $design-team-review 评审这个页面，在独立图层里标注问题。文案简短，使用带底色的 P0/P1/P2/P3 标签，不改原稿。

每次评审报告记录本次 skill 的 Git 提交版本，便于复核。工具没有读取本地 Git 的能力时标记“版本未知”，不编造版本号。

## 本地验证

在仓库根目录运行以下命令；测试文件位于指定 iCloud 临时工作目录，并在测试结束清理：

```bash
DPR_TEST_ROOT="$HOME/Library/Mobile Documents/com~apple~CloudDocs/🧬chatGPT/临时工作/skill-sync-tests" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

## 仓库改名后的旧安装迁移

新地址：https://github.com/HMinsholiday/design-team-review

已安装的同事无需删除技能。旧更新器仍保存旧地址校验规则，请先更新源码，再重新运行安装器，一次性刷新远程地址和本机更新器：

```bash
git -C "$HOME/Library/Mobile Documents/com~apple~CloudDocs/🧬chatGPT/新项目/设计团队内部AI预评共享" pull --ff-only https://github.com/HMinsholiday/design-team-review.git main
python3 "$HOME/Library/Mobile Documents/com~apple~CloudDocs/🧬chatGPT/新项目/设计团队内部AI预评共享/scripts/install.py"
```

执行前确认没有本地修改；有修改时先保留并处理，不强制覆盖。新版更新器只兼容本仓库明确的旧地址，成功快进更新后迁移 origin，不接受其他仓库地址。自定义安装路径者使用实际路径和原安装参数。尚未安装者直接按上方新地址安装即可。

## Skill 名称更新

调用名称统一为 `$design-team-review`，主目录为 `design-team-review/`。`design-pre-review` 仅为旧安装保留兼容软链接，勿重复安装两份。原安装入口在支持软链接的环境中会读到新 skill 名称；重新运行安装器可将同仓库旧入口迁移为新名称。独立副本不会被覆盖。后台服务和状态目录保留旧技术标识，避免重复启动更新任务。

## 更新频率调整

当前默认每小时检查一次（间隔 3600 秒），到期后登录补查。此前安装了每 5 分钟检查的用户，需要先拉取仓库新版，再重新运行安装器，才能更新本机 LaunchAgent；仅 skill 文件同步不会改变旧定时任务。安装器会替换同名任务，不重复新增任务。

## 团队统一控制检查周期

维护者修改根目录 `sync-config.json` 的 `check_interval_seconds`：86400 为每日，3600 为每小时。维护者完成调整并检查通过后自动提交推送；尚未推送的本地修改不影响其他人。配置值支持 60～2592000 秒整数。

新版后台任务每分钟仅在本机判断是否到期，不联网；到期才检查 Git 并同步。成功同步后读取新周期，安排下一次检查。因此从每日改为每小时，需等旧的每日检查发现新版后生效，不能立即推送到离线电脑。失败后按当前周期重试，手动运行 update.py 可立即重试。配置无效时不联网更新，日志会说明原因；先修复本地配置或手动拉取修复版。

已安装旧更新器的同事需一次性拉取新版并重新运行安装器，启用这个机制。此后仅调整检查周期无需同事操作。安装器重装不会重置已保存的到期时间。日志与 schedule.json 存在本机状态目录，不进入 Git。
