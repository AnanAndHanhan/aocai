# 澳彩项目恢复指南

本文档用于在新电脑上完整恢复“澳彩”项目，包括 GitHub 克隆、基础依赖、Ollama、本地模型、运行验证和后续开发流程。

> 项目说明：本项目是 Markdown 知识库 + 本地 AI 分析工作流，不是 Web 应用。恢复完成后，主要通过阅读和维护 Markdown 文件继续项目；需要分析图片资料时，再运行 `ai-workflow/` 下的脚本。

## 1. 新电脑如何恢复整个项目

推荐恢复路径：

1. 安装基础工具：Homebrew、Git、GitHub CLI、Python 3、Ollama。
2. 登录 GitHub，确保有访问仓库的权限。
3. 从 GitHub 克隆项目到本地。
4. 启动 Ollama 服务。
5. 拉取并验证本地模型。
6. 阅读项目文档，运行一次脚本确认工作流可用。

建议恢复目录：

```bash
mkdir -p ~/Documents
git clone https://github.com/AnanAndHanhan/aocai.git ~/Documents/澳彩
cd ~/Documents/澳彩
```

恢复后优先阅读：

1. `README.md`
2. `PROJECT_HANDOFF.md`
3. `基础资料.md`
4. `决策记录.md`
5. `项目记忆.md`
6. `开奖记录.md`

## 2. 如何从 GitHub 克隆项目

仓库地址：

```text
https://github.com/AnanAndHanhan/aocai.git
```

如果仓库是私有仓库，先安装并登录 GitHub CLI：

```bash
gh auth login
gh auth status
```

然后克隆：

```bash
git clone https://github.com/AnanAndHanhan/aocai.git ~/Documents/澳彩
cd ~/Documents/澳彩
```

确认远程仓库和分支：

```bash
git remote -v
git status --short --branch
```

正常应看到：

```text
origin  https://github.com/AnanAndHanhan/aocai.git (fetch)
origin  https://github.com/AnanAndHanhan/aocai.git (push)
## main...origin/main
```

如果 GitHub 暂时不可用，也可以从本地 bundle 恢复：

```bash
git clone 澳彩-backup.bundle ~/Documents/澳彩-restored
```

bundle 只是备份兜底；日常恢复优先使用 GitHub 仓库。

## 3. 如何安装依赖

### macOS 基础依赖

安装 Homebrew：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Apple Silicon Mac 通常需要把 Homebrew 加入 shell 环境：

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Intel Mac 的 Homebrew 路径通常是 `/usr/local/bin/brew`。如果不确定，运行：

```bash
command -v brew
brew --version
```

安装项目所需工具：

```bash
brew install git gh python ollama
```

确认版本：

```bash
git --version
gh --version
python3 --version
ollama --version
```

当前项目脚本主要使用 Python 标准库，不需要额外安装 Python 第三方依赖。

## 4. 如何安装和配置 Ollama

如果使用 Homebrew 安装：

```bash
brew install ollama
```

启动 Ollama 服务：

```bash
brew services start ollama
```

如果 `brew services start ollama` 不可用，可以在一个独立终端里运行：

```bash
ollama serve
```

确认服务是否可访问：

```bash
curl http://127.0.0.1:11434/api/tags
```

正常情况下会返回 JSON。项目默认 Ollama 地址写在：

```text
ai-workflow/config/models.json
```

当前配置：

```json
{
  "ollama_base_url": "http://127.0.0.1:11434",
  "models": {
    "main": "qwen3:14b-q4_K_M",
    "vision": "qwen2.5vl:7b-q4_K_M"
  }
}
```

如果新电脑的 Ollama 不在 `127.0.0.1:11434`，需要同步修改 `ai-workflow/config/models.json`。

## 5. 如何安装并恢复 Qwen3 模型

本项目主分析模型：

```text
qwen3:14b-q4_K_M
```

Vision 图片识别模型：

```text
qwen2.5vl:7b-q4_K_M
```

拉取模型：

```bash
ollama pull qwen3:14b-q4_K_M
ollama pull qwen2.5vl:7b-q4_K_M
```

确认模型已安装：

```bash
ollama list
```

快速验证 Qwen3：

```bash
curl http://127.0.0.1:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3:14b-q4_K_M",
    "prompt": "请只回复：模型已恢复",
    "stream": false,
    "think": false
  }'
```

如果返回 JSON 中的 `response` 有内容，说明 Qwen3 可用。

快速验证 Vision 模型：

```bash
ollama list | grep qwen2.5vl
```

完整 Vision 验证通常需要图片输入，可在项目恢复后用 `ai-workflow/tests/assets/vision-redbox-test.svg.png` 运行脚本验证。

模型占用空间较大。恢复前建议至少预留 25GB 以上可用磁盘空间：

```bash
df -h
```

## 6. 如何启动整个项目

本项目没有常驻 Web 服务。所谓“启动项目”分为两类：打开知识库继续维护，或运行本地 AI 分析工作流。

### 打开知识库

进入项目目录：

```bash
cd ~/Documents/澳彩
```

查看当前状态：

```bash
git status --short --branch
```

按顺序阅读和维护文档：

```text
README.md
PROJECT_HANDOFF.md
基础资料.md
决策记录.md
项目记忆.md
开奖记录.md
```

### 运行单图分析

传入一张图片：

```bash
./ai-workflow/scripts/run_analysis.sh 图片路径
```

也可以把图片放入：

```text
ai-workflow/inbox/
```

然后运行：

```bash
./ai-workflow/scripts/run_analysis.sh
```

输出位置：

```text
ai-workflow/outputs/<run-id>/vision_extract.md
ai-workflow/outputs/<run-id>/final_analysis.md
```

### 运行多资料交叉分析

推荐使用多资料流程：

```bash
./ai-workflow/scripts/run_period.sh 期号 图片1 图片2 ...
```

示例：

```bash
./ai-workflow/scripts/run_period.sh 2026-178 image1.png image2.png
```

最终输出：

```text
ai-workflow/output/<期号>/当期分析.md
```

### 运行一次内置测试图片

项目内有测试图片：

```text
ai-workflow/tests/assets/vision-redbox-test.svg.png
```

可以用它验证模型、脚本和输出目录：

```bash
./ai-workflow/scripts/run_period.sh test-restore ai-workflow/tests/assets/vision-redbox-test.svg.png
```

执行后检查：

```bash
ls -la ai-workflow/output/test-restore/
```

## 7. 常见错误及解决方法

### `git: command not found`

说明 Git 未安装或 PATH 未生效。

```bash
brew install git
exec zsh
git --version
```

### `repository not found` 或 GitHub 无权限

常见原因是未登录 GitHub、账号无权限或仓库地址写错。

```bash
gh auth login
gh auth status
git remote -v
```

确认仓库地址是：

```text
https://github.com/AnanAndHanhan/aocai.git
```

### `ollama: command not found`

说明 Ollama 未安装或 PATH 未生效。

```bash
brew install ollama
exec zsh
ollama --version
```

### `Failed to connect to 127.0.0.1 port 11434`

说明 Ollama 服务没有启动。

```bash
brew services start ollama
curl http://127.0.0.1:11434/api/tags
```

如果服务方式不可用，开一个终端运行：

```bash
ollama serve
```

### `model not found`

说明本地没有对应模型，或模型名与配置不一致。

```bash
ollama pull qwen3:14b-q4_K_M
ollama pull qwen2.5vl:7b-q4_K_M
ollama list
cat ai-workflow/config/models.json
```

### Qwen3 返回空内容

对部分推理模型，短测试可能把内容放入思考段或返回不可见内容。测试时显式设置：

```json
"think": false
```

项目配置中已经设置：

```json
"think": false
```

### Vision 请求报上下文不足或 HTTP 400

高分辨率图片可能超出默认上下文。项目配置中 Vision 上下文为：

```json
"num_ctx_vision": 8192
```

如果仍失败，先压缩图片尺寸，或继续提高 `ai-workflow/config/models.json` 中的 `num_ctx_vision`。

### `No images provided and ai-workflow/inbox has no image files`

说明没有传入图片，`inbox` 里也没有图片。

解决方法：

```bash
./ai-workflow/scripts/run_analysis.sh 图片路径
```

或把图片放入：

```text
ai-workflow/inbox/
```

### `Permission denied`

脚本没有执行权限时，重新赋权：

```bash
chmod +x ai-workflow/scripts/*.sh
chmod +x ai-workflow/scripts/*.py
```

### 中文路径或文件名出错

命令里包含中文路径或空格时，用引号包住路径：

```bash
./ai-workflow/scripts/run_period.sh 2026-178 "图片路径/资料图.png"
```

### `git push` 被拒绝

先拉取远端最新提交：

```bash
git pull --ff-only origin main
```

如果不能 fast-forward，说明本地和远端都有新提交，需要先检查差异并手动合并，确认无误后再推送。

## 8. 如何继续开发

每次开发前先同步远端：

```bash
git pull --ff-only origin main
```

查看当前状态：

```bash
git status --short --branch
```

常见维护内容：

- 更新 `CHANGELOG.md`：每次开发任务完成后记录新增功能、修改内容和修复问题。
- 更新 `开奖记录.md`：新增期数、日期、正码、特码、首号生肖、特码生肖和走势摘要。
- 更新 `基础资料.md`：补充生肖资料、规则和实战复盘。
- 更新 `决策记录.md`：记录已确认的分析口径和边界规则。
- 更新 `ai-workflow/prompts/`：调整 Vision 或主模型提示词。
- 更新 `ai-workflow/scripts/`：改进本地分析流程和自动化。

提交并推送：

```bash
git status --short --branch
# 确认 CHANGELOG.md 已记录本次开发任务
git add -A
git commit -m "Update 澳彩 project"
git push origin main
```

注意事项：

- `ai-workflow/cache/` 和 `ai-workflow/logs/` 默认不上传。
- 每次完成开发任务后，必须先更新 `CHANGELOG.md`，再提交推送。
- 临时文件、`.env`、`__pycache__`、日志文件不要提交。
- 正式分析结果保存到 `ai-workflow/output/<期号>/当期分析.md`。
- 重要规则必须写入 `决策记录.md` 或 `基础资料.md`，不要只留在聊天记录里。
- 每期开奖后优先维护 `开奖记录.md`，下一期分析前必须复核上一期首号生肖。

## 9. 恢复完成检查清单

恢复完成后依次确认：

```bash
cd ~/Documents/澳彩
git status --short --branch
git remote -v
python3 --version
ollama list
curl http://127.0.0.1:11434/api/tags
./ai-workflow/scripts/run_period.sh test-restore ai-workflow/tests/assets/vision-redbox-test.svg.png
```

如果以上命令都能正常完成，新电脑上的项目恢复就完成了。
