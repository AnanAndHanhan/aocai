# 澳彩项目恢复与同步

更新时间：2026-10-31

安装 Git 和 Markdown 编辑器。需要使用 GitHub CLI 时安装 gh 并完成授权：

```bash
gh auth login
gh auth setup-git
git clone https://github.com/AnanAndHanhan/aocai.git
cd aocai
git status --short --branch
```

若目录已有仓库，先检查未提交修改，再使用 `git pull --ff-only origin main` 同步。不要覆盖用户已有修改。

依次阅读 README.md、PROJECT_HANDOFF_FINAL.md、基础资料.md、决策记录.md、开奖记录.md；核对最新规则与记录日期后继续任务。

维护后更新 CHANGELOG.md，使用 `git diff --check` 和 `git diff` 检查，仅暂存相关文件，提交后 `git push origin main`。确认远程 main 与本地 HEAD 一致。

交付压缩包是当前文件快照，不包含 Git 历史；完整历史可从仓库克隆恢复。
