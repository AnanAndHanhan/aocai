# 澳彩项目

本项目是一个用于维护澳门六合彩生肖卡资料、开奖记录、分析规则和本地 AI 分析流程的知识库项目。项目内容以 Markdown 文档为核心，并包含一套基于 Ollama 的本地图片识别与多资料交叉分析脚本。

> 说明：项目中的分析、复盘和规则整理仅用于资料归档、文本分析和娱乐性统计参考，不构成投注建议、收益承诺或任何形式的投资建议。

## 项目介绍

“澳彩”项目主要解决三件事：

1. 沉淀基础资料：保存 2026 年生肖号码、主格、生肖外号、分组、资料图分析口径和实战复盘。
2. 维护开奖记录：记录期数、日期、正码、特码、首号生肖、特码生肖和近期开奖走势。
3. 支持本地 AI 分析：通过本地 Ollama 模型完成资料图 OCR、红框/有效区域提取、brief 汇总和多资料交叉分析。

项目不是传统 Web 服务，也没有前端页面或后端 API。大多数情况下，直接阅读和维护 Markdown 文件即可；需要处理图片资料时，再运行 `ai-workflow/` 下的脚本。

## 项目结构

```text
.
├── README.md
├── PROJECT_HANDOFF.md
├── 基础资料.md
├── 决策记录.md
├── 项目记忆.md
├── 对话摘要.md
├── 开奖记录.md
├── 澳彩-backup.bundle
└── ai-workflow/
    ├── README.md
    ├── config/
    │   ├── models.json
    │   └── workflow.json
    ├── inbox/
    ├── input/
    ├── output/
    ├── outputs/
    ├── prompts/
    ├── scripts/
    └── tests/
```

核心文件说明：

| 路径 | 作用 |
| --- | --- |
| `README.md` | 项目总入口，说明安装、运行和维护方式 |
| `PROJECT_HANDOFF.md` | 完整交接文档，新会话或新设备接手时优先阅读 |
| `基础资料.md` | 核心资料库：生肖号码、主格、外号、分组、分析规则和复盘 |
| `决策记录.md` | 已确认的分析规则、权重边界和输出格式 |
| `项目记忆.md` | 项目位置、备份目标、接手顺序和维护原则 |
| `对话摘要.md` | 早期对话与备份方案摘要 |
| `开奖记录.md` | 开奖数据库、近 50 期走势摘要和明细 |
| `澳彩-backup.bundle` | 本地 Git bundle 备份文件 |
| `ai-workflow/` | 本地 AI 工作流配置、脚本、提示词、输入和输出目录 |

## 所需环境

基础维护只需要：

- Git
- 能编辑 Markdown 的文本编辑器

运行本地 AI 工作流还需要：

- macOS 或类 Unix shell 环境
- Python 3
- Ollama
- 本地模型：
  - `qwen3:14b-q4_K_M`
  - `qwen2.5vl:7b-q4_K_M`

当前脚本主要使用 Python 标准库调用 Ollama HTTP API，不需要额外安装 Python 第三方依赖。图片尺寸读取在 macOS 上会调用系统自带的 `sips`；如果其他系统没有 `sips`，脚本会记录提示但不影响主要流程。

## 如何安装

### 1. 克隆仓库

```bash
git clone https://github.com/AnanAndHanhan/aocai.git
cd aocai
```

### 2. 安装基础工具

macOS 上推荐使用 Homebrew：

```bash
brew install git gh ollama
```

如果只维护 Markdown 文件，不运行 AI 工作流，可以只安装 Git。

### 3. 安装本地模型

启动 Ollama 后拉取模型：

```bash
ollama pull qwen3:14b-q4_K_M
ollama pull qwen2.5vl:7b-q4_K_M
```

确认 Ollama 服务地址为：

```text
http://127.0.0.1:11434
```

模型和上下文配置位于：

```text
ai-workflow/config/models.json
```

## 如何运行

### 资料维护流程

新会话或新设备接手时，建议按顺序阅读：

1. `README.md`
2. `PROJECT_HANDOFF.md`
3. `基础资料.md`
4. `决策记录.md`
5. `项目记忆.md`
6. `开奖记录.md`

每期开奖后，先更新 `开奖记录.md`，再根据需要补充 `决策记录.md`、`基础资料.md` 或复盘内容。下一期分析前，必须从 `开奖记录.md` 复核上一期开奖结果第一颗号码对应生肖，首号用于最高降权；末尾特码不能误当首号降权。

### 单图分析

直接传入一张图片：

```bash
./ai-workflow/scripts/run_analysis.sh 图片路径
```

如果不传图片路径，脚本会读取：

```text
ai-workflow/inbox/
```

单图输出位置：

```text
ai-workflow/outputs/<run-id>/vision_extract.md
ai-workflow/outputs/<run-id>/final_analysis.md
```

### 多资料交叉分析

推荐使用多资料交叉流程：

```bash
./ai-workflow/scripts/run_period.sh 期号 图片1 图片2 ...
```

示例：

```bash
./ai-workflow/scripts/run_period.sh 2026-178 image1.png image2.png
```

执行流程：

1. 每张图片调用 `qwen2.5vl:7b-q4_K_M` 做 OCR 和图像线索提取。
2. `build_brief.py` 汇总单图结果，生成 `ai-workflow/cache/<期号>/brief.md`。
3. `cross_analyze.py` 读取 `PROJECT_HANDOFF.md`、`基础资料.md`、`决策记录.md` 和 `brief.md`。
4. `qwen3:14b-q4_K_M` 输出最终多资料交叉分析。

最终输出位置：

```text
ai-workflow/output/<期号>/当期分析.md
```

## GitHub 仓库说明

当前 GitHub 仓库：

```text
https://github.com/AnanAndHanhan/aocai.git
```

当前主分支：

```text
main
```

常用命令：

```bash
git status --short --branch
git pull --ff-only origin main
git add -A
git commit -m "Update project docs"
git push origin main
```

`.gitignore` 已排除缓存、日志、`__pycache__`、环境变量文件和临时文件。`ai-workflow/cache/` 与 `ai-workflow/logs/` 默认不上传，只保留 `.gitkeep` 目录占位；正式分析结果应保存到 `ai-workflow/output/` 或项目 Markdown 文档中。

## 后续开发计划

建议后续按优先级推进：

1. 完善 `开奖记录.md` 自动更新脚本，减少手动录入和统计误差。
2. 为 `ai-workflow/scripts/` 增加最小化测试，覆盖图片路径解析、brief 生成和输出文件落盘。
3. 将常用运行命令封装为统一入口，例如 `make analyze-period` 或一个顶层脚本。
4. 增加模型连通性检查命令，提前验证 Ollama 服务、模型名称和上下文配置。
5. 把每期最终结果、复盘结论和新增规则形成固定维护流程，及时写回 `开奖记录.md`、`决策记录.md` 和 `基础资料.md`。
6. 保持仓库定期推送到 GitHub，并在重大规则更新后同步生成本地 bundle 备份。
