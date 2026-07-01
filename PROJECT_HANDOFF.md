# 澳彩项目交接文档

- 更新日期：2026-07-01
- 项目路径：`/Users/anan/Documents/澳彩`
- GitHub 仓库：`https://github.com/AnanAndHanhan/aocai.git`
- 当前主分支：`main`

> 本项目用于整理澳门六合彩生肖卡基础资料、开奖记录、分析规则、对话记忆、实战复盘和本地 AI 分析流程。开奖具有随机性，所有推演仅作资料归档、文本分析和娱乐性统计参考，不构成投注建议、收益承诺或投资建议。

## 1. 项目状态总览

“澳彩”当前是一个 Markdown 知识库 + 本地 AI 工作流项目，不是传统 Web 应用，也没有需要常驻启动的前后端服务。

当前已完成：

- Git 仓库已初始化，主分支为 `main`。
- 远程仓库已切换并推送到 `https://github.com/AnanAndHanhan/aocai.git`。
- `README.md` 已生成，作为项目总入口。
- `RESTORE.md` 已生成，作为新电脑恢复指南。
- `PROJECT_HANDOFF.md` 已更新为当前交接文档。
- `.gitignore` 已配置，排除缓存、日志、`__pycache__`、环境变量和临时文件。
- `开奖记录.md` 已作为独立开奖数据库维护，当前接口最新记录写到 2026 年第 182 期。
- `ai-workflow/` 本地 AI 工作流已推进到 Phase 3：支持多资料逐图 Vision 提取、brief 汇总、Qwen3 多资料交叉分析和结果落盘。

当前 Git 状态要求：

- 本文件更新并提交推送后，`git status --short --branch` 应显示 `## main...origin/main`，没有未提交文件。
- 后续任何规则、资料、开奖记录或脚本变更，都应提交并推送到 GitHub。

## 2. 项目目录结构

```text
.
├── .gitignore
├── README.md
├── RESTORE.md
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

| 路径 | 当前作用 | 接手优先级 |
| --- | --- | --- |
| `README.md` | 项目总入口，说明项目定位、安装、运行、GitHub 仓库和开发计划 | 最高 |
| `RESTORE.md` | 新电脑恢复指南，覆盖克隆、依赖、Ollama、模型和验证 | 最高 |
| `PROJECT_HANDOFF.md` | 本交接文档，概括当前状态、结构、进度、待办和设计决策 | 最高 |
| `基础资料.md` | 核心资料库：生肖号码、主格、外号、分组、分析规则和实战复盘 | 最高 |
| `决策记录.md` | 已确认的分析规则、权重边界、开奖记录维护规则和输出格式 | 高 |
| `项目记忆.md` | 项目位置、备份目标、交接顺序和开奖记录维护原则 | 高 |
| `开奖记录.md` | 开奖数据库、近 50 期走势摘要、近 10 期窗口和明细 | 高 |
| `对话摘要.md` | 早期对话和备份方案摘要 | 中 |
| `澳彩-backup.bundle` | 本地 Git bundle 备份文件，作为 GitHub 不可用时的兜底恢复来源 | 备份用 |
| `ai-workflow/` | 本地 AI 分析工作流：配置、脚本、提示词、输入输出和测试资源 | 高 |

当前没有 `.codex`、`.agents` 或类似 AI 客户端状态目录。项目可迁移内容应以仓库文件为准；历史聊天、账号级记忆和本机软件状态不应被当作项目恢复的唯一来源。

## 3. GitHub 与备份状态

当前远程仓库：

```text
origin https://github.com/AnanAndHanhan/aocai.git
```

本次更新前已推送的关键提交：

```text
5b30c45 Add project restore guide
3a05d02 Add project README
1f952e7 Backup 澳彩 project
428ac18 初始备份澳彩资料
```

常用命令：

```bash
git status --short --branch
git pull --ff-only origin main
git add -A
git commit -m "Update 澳彩 project"
git push origin main
```

备份策略：

- GitHub 仓库是主备份和跨设备同步来源。
- `澳彩-backup.bundle` 是本地离线兜底备份。
- 重大规则变更、开奖记录更新、脚本调整、README/RESTORE/HANDOFF 更新后，都要提交并推送。
- 不要提交 `ai-workflow/cache/`、`ai-workflow/logs/`、`.env`、`__pycache__` 和临时文件。

从 GitHub 恢复：

```bash
git clone https://github.com/AnanAndHanhan/aocai.git ~/Documents/澳彩
cd ~/Documents/澳彩
```

从 bundle 兜底恢复：

```bash
git clone 澳彩-backup.bundle ~/Documents/澳彩-restored
```

完整恢复流程以 `RESTORE.md` 为准。

## 4. 开发进度

### 文档与知识库

已完成：

- `基础资料.md`：已整理 2026 年生肖号码、主格、VIP 底栏、生肖外号、常用分组、补充分组、代表汇总、名人生肖和实战复盘。
- `决策记录.md`：已记录备份方式、资料图分析口径、数字串分析、澳门挂牌规则、开奖记录维护、龙线识别、“首”字、“阳”字、单个中文数字双拆和最终输出格式。
- `开奖记录.md`：已建立独立开奖数据库，当前记录显示接口最新为 2026 年第 182 期，并维护近 50 期、近 10 期摘要。
- `README.md`：已完成项目说明、结构、安装、运行、环境、GitHub 仓库和后续计划。
- `RESTORE.md`：已完成新电脑恢复手册，覆盖依赖、Ollama、模型、运行验证和常见错误。

### 本地 AI 工作流

当前工作流目录：`ai-workflow/`

已完成阶段：

- Phase 1：Ollama 主模型和 Vision 模型验证，目录骨架建立。
- Phase 2：单图输入、Vision OCR、决策记录范围裁剪、Qwen3 主分析和输出落盘串联。
- Phase 3：多资料逐图 Vision、`brief.md` 汇总、Qwen3 多资料交叉分析和 `output/期号/当期分析.md` 输出串联。

当前模型配置位于 `ai-workflow/config/models.json`：

```json
{
  "ollama_base_url": "http://127.0.0.1:11434",
  "models": {
    "main": "qwen3:14b-q4_K_M",
    "vision": "qwen2.5vl:7b-q4_K_M"
  },
  "defaults": {
    "temperature": 0.2,
    "top_p": 0.9,
    "num_ctx_main": 32768,
    "num_ctx_vision": 8192,
    "think": false
  }
}
```

主要脚本：

| 脚本 | 作用 |
| --- | --- |
| `ai-workflow/scripts/run_analysis.sh` | Phase 2 单图分析入口 |
| `ai-workflow/scripts/run_period.sh` | Phase 3 多资料交叉分析入口 |
| `ai-workflow/scripts/vision_extract.py` | 调用 Vision 模型提取 OCR 和图像事实 |
| `ai-workflow/scripts/build_brief.py` | 合并多图结构化结果并生成 brief |
| `ai-workflow/scripts/cross_analyze.py` | 调用 Qwen3 做多资料交叉分析 |
| `ai-workflow/scripts/common.py` | 共享配置、Ollama 请求、文件读写和日志工具 |

运行多资料交叉分析：

```bash
./ai-workflow/scripts/run_period.sh 期号 图片1 图片2 ...
```

测试恢复流程：

```bash
./ai-workflow/scripts/run_period.sh test-restore ai-workflow/tests/assets/vision-redbox-test.svg.png
```

## 5. 重要设计决策

### Git + Markdown 作为长期记忆

项目决定采用“Git 私有仓库 + 项目内 Markdown 文件”的方式备份和迁移上下文。

原因：

- Markdown 文件透明、可读、可迁移。
- Git 适合跨设备、跨账号同步。
- AI 对话和账号记忆不可靠，重要规则必须沉淀到仓库文件。

### 项目不是 Web 应用

当前没有前端页面、后端服务、数据库迁移或 Node 依赖。接手人不要先找应用入口，应先阅读 Markdown 文件和 `ai-workflow/README.md`。

### Ollama 本地模型优先

本地 AI 分析使用 Ollama：

- 主分析模型：`qwen3:14b-q4_K_M`
- Vision 模型：`qwen2.5vl:7b-q4_K_M`
- 默认服务：`http://127.0.0.1:11434`
- 对 Qwen3 测试和分析设置 `"think": false`，避免短测试输出被思考段吞掉。

### 缓存和日志不作为长期资产

`.gitignore` 默认排除：

- `ai-workflow/cache/*`
- `ai-workflow/logs/*`
- `__pycache__/`
- `*.log`
- `.env`
- 临时文件

正式可交接结果应进入：

- `开奖记录.md`
- `基础资料.md`
- `决策记录.md`
- `ai-workflow/output/<期号>/当期分析.md`
- 其他明确需要长期保存的 Markdown 文档

### 资料图分析规则

所有资料图分析遵循：

- 用户红框/指定区域优先。
- 未标注、被用户明确排除或规则默认排除的区域不参与排序和权重。
- 先整体释义，再拆关键词、字形、数字、生肖、五行、家野、山水、天地和号码级线索。
- 解肖和九肖只能作为弱辅助候选池，不能压过正文、图画、诗句、成语、数字串、幽默言外之意和号码级交叉。
- 暗码默认不看，除非用户明确要求。

### 开奖记录与降权规则

`开奖记录.md` 是下一期分析前必须复核的数据库。

固定规则：

- 每期开奖后先更新 `开奖记录.md`。
- 记录期数、日期、六码正码、特码、首号及首号生肖、特码及特码生肖。
- 下一期最高降权只看上一期开奖结果第一颗号码对应生肖。
- 末尾特码只能用于复盘和走势统计，不能误当首号降权。
- 历史 50 期走势只作辅助，不能压过当期资料逐字分析和多资料交叉。

### 最终输出格式

每期最终结论必须固定分为：

- 主六肖：按 1-6 排序。
- 防三肖：按 1-3 排序。

每个生肖后必须用一句话说明关键资料支撑和交叉，至少包含资料来源、关键词/句、号码级线索或分类线；有降权必须注明。禁止只输出生肖名单，也禁止只写“交叉多、资料明显”等泛泛理由。

## 6. 接手阅读顺序

新设备、新账号或新会话接手时，按以下顺序阅读：

1. `README.md`
2. `RESTORE.md`
3. `PROJECT_HANDOFF.md`
4. `基础资料.md`
5. `决策记录.md`
6. `项目记忆.md`
7. `开奖记录.md`
8. `ai-workflow/README.md`

接手后先确认：

- 当前 Git 状态是否干净。
- 是否已经拉取 `origin/main` 最新提交。
- `开奖记录.md` 的接口最新期数和本地最新期数是否一致。
- 用户是否已上传当期资料图、红框区域、上期开奖结果和对冲生肖。
- 当期是否有用户明确排除的资料区域；若有，以用户当期说明为准。

## 7. 当期分析标准流程

建议每期按下面顺序执行：

1. 确认期数、资料类型、用户红框/指定区域。
2. 更新或核对 `开奖记录.md`。
3. 确认上一期开奖结果第一颗号码及生肖，单独记录末尾特码，防止混淆。
4. 确认当期对冲生肖。
5. 按资料类型逐图分析：先整体释义，再拆字、数字、图像、场景、五行、家野、山水、外号。
6. 汇总候选生肖，标明每个生肖来自哪些独立线索。
7. 对高频或强线候选逐一做号码级检查：号码本肖、波色、主外号、五行、右下角生肖、VIP 底栏。
8. 应用上期首号和对冲降权，但只做相对降权，不做绝对排除。
9. 输出主六肖、防三肖，每个生肖必须附一句清晰理由。
10. 开奖后复盘并把新规则或错误修正写回 `决策记录.md` 或 `基础资料.md`。

## 8. 待办事项

优先级较高：

- 完善 `开奖记录.md` 自动更新脚本，减少手动录入和统计误差。
- 把 `aczj.cc` 接口拉取、缺失期数补齐、近 50 期/近 10 期摘要重算流程固化为项目脚本。
- 为 `ai-workflow/scripts/` 增加最小化测试，覆盖图片路径解析、brief 生成、Ollama 请求失败和输出落盘。
- 增加模型健康检查脚本，验证 Ollama 服务、`qwen3:14b-q4_K_M`、`qwen2.5vl:7b-q4_K_M`、上下文配置和 `"think": false`。

中期优化：

- 将常用命令封装为统一入口，例如 `make analyze-period` 或顶层 `scripts/` 命令。
- 清理或归档早期 Phase 测试输出，明确哪些结果需要长期保留。
- 为 `RESTORE.md` 增加 Windows/Linux 差异说明，如果未来要跨平台恢复。
- 在每次重大规则更新后同步更新 README、RESTORE 和 HANDOFF，避免交接文档再次过期。

长期维护：

- 每期开奖后优先维护 `开奖记录.md`。
- 每次分析发现规则边界或漏判原因，都写入 `决策记录.md`。
- 实战复盘和资料补充写入 `基础资料.md`。
- 保持 GitHub 仓库定期推送，并定期刷新本地 bundle 备份。

## 9. 常见风险

- 把末尾特码误当作首号生肖：必须从 `开奖记录.md` 表格中的“首号”列复核。
- 只看单字拆解，忽略整句、成语或幽默包袱：分析必须先整体释义。
- 过度相信解肖/九肖：它们只能作为弱辅助候选池。
- 使用历史走势直接决定结果：近 50 期和近 10 期只能辅助，不能压过当期资料。
- 忘记提交推送：重要文档和脚本变化必须进入 GitHub。
- 依赖本机聊天记忆：重要上下文必须写入仓库 Markdown。
- 新电脑恢复后忘记拉模型：`RESTORE.md` 中的 Ollama 和模型检查必须执行。

## 10. 给新会话的推荐开场提示

可以直接给新 AI 会话如下提示：

```text
请接手 /Users/anan/Documents/澳彩 项目。先阅读 README.md、RESTORE.md、PROJECT_HANDOFF.md、基础资料.md、决策记录.md、项目记忆.md、开奖记录.md 和 ai-workflow/README.md。这个项目是 Markdown 知识库 + Ollama 本地 AI 工作流，不是 Web 应用。后续分析资料图时，必须按用户红框/指定区域优先，先整体释义再拆字和数字；开奖记录里的首号用于下一期最高降权，末尾特码不能当首号。最终输出必须分为主六肖和防三肖，并给每个生肖一句具体支撑理由。
```
