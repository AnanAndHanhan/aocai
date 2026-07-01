# 澳彩本地 AI 工作流

本目录用于保存完全本地运行的 AI 工作流配置、提示词、脚本、输入图片、输出结果和日志。

当前状态：

- Phase 1 已完成：Ollama 主模型和 Vision 模型已验证，目录骨架已建立。
- Phase 2 已完成：图片输入、Vision OCR、决策记录范围裁剪、Qwen3 主分析和输出落盘已串联。
- Phase 3 已完成：多资料逐图 Vision、brief.md 汇总、Qwen3 多资料交叉分析和 `output/期号/当期分析.md` 输出已串联。

Phase 1 目标：

1. 保留 `qwen3:14b-q4_K_M` 作为主分析模型。
2. 安装并验证 `qwen2.5vl:7b-q4_K_M` 作为 Vision 模型。
3. 建立项目内目录骨架，方便后续备份和迁移。

Phase 1 验证结论：

- `qwen2.5vl:7b-q4_K_M` 已可通过 Ollama Vision API 识别图片、红框和数字。
- 对高分辨率图片必须显式设置 Vision 上下文，例如 `num_ctx: 8192`；默认 4096 可能导致请求超过上下文而返回 400。
- OCR 对易混汉字可能受图片分辨率影响。低分辨率测试中曾把“隈”误读为“限”，高分辨率加 `num_ctx: 8192` 后识别正确。

目录说明：

- `config/`: 模型和工作流配置。
- `input/`: 建议按期号保存原始图片，例如 `input/2026-178/`。
- `prompts/`: Vision 提取和主模型分析提示词。
- `scripts/`: 本地运行脚本。
- `inbox/`: Phase 2 兼容入口，未指定图片时读取这里。
- `output/`: Phase 3 正式分析结果，按期号保存。
- `outputs/`: Phase 2 兼容输出目录。
- `logs/`: 后续放运行日志。
- `cache/`: 后续放 OCR 和中间结构化结果。
- `tests/assets/`: 放本地验证用图片。

Phase 2 命令：

```bash
/Users/anan/Documents/澳彩/ai-workflow/scripts/run_analysis.sh 图片路径
```

如果不传图片路径，脚本会读取 `ai-workflow/inbox/` 中的图片。

Phase 2 输出：

- `ai-workflow/cache/<run-id>/vision_extract.json`: Vision 结构化事实提取结果。
- `ai-workflow/cache/<run-id>/qwen3_analysis.json`: Qwen3 原始响应和元数据。
- `ai-workflow/outputs/<run-id>/vision_extract.md`: Vision 人类可读结果。
- `ai-workflow/outputs/<run-id>/final_analysis.md`: 最终分析结果。

Phase 2 范围规则：

- 人工红框或用户指定区域优先。
- 用户没有特别标注红框时，脚本按 `PROJECT_HANDOFF.md`、`基础资料.md`、`决策记录.md` 的资料类型口径自动确定有效范围。
- 管家婆自动只取“一句话赢大钱：”冒号后的红字句；平特玄机、上期回放、解码和号码默认排除。
- 跑马图、跑狗图、澳门跑狗无人工红框时保留资料类型有效区域；暗码默认排除。
- 解肖和九肖只进入弱辅助字段，不能单独作为主权重。
- 上期开奖结果、末尾特码和当期对冲信息只进入降权上下文字段，不能当成本期数字线抬权。

Phase 3 多资料交叉命令：

```bash
/Users/anan/Documents/澳彩/ai-workflow/scripts/run_period.sh 期号 图片1 图片2 ...
```

示例：

```bash
/Users/anan/Documents/澳彩/ai-workflow/scripts/run_period.sh 2026-178 image1.png image2.png
```

Phase 3 执行流程：

1. 每张图片单独调用 `qwen2.5vl:7b-q4_K_M`，只做 OCR 和图像线索提取，不做最终分析。
2. 每张图保存结构化 Vision JSON。
3. `build_brief.py` 合并所有单图结构化结果，生成 `ai-workflow/cache/<期号>/brief.md`。
4. `cross_analyze.py` 调用 `qwen3:14b-q4_K_M`，读取 `PROJECT_HANDOFF.md`、`基础资料.md`、`决策记录.md` 和 `brief.md`。
5. 最终保存到 `ai-workflow/output/<期号>/当期分析.md`。

Phase 3 输出：

- `ai-workflow/cache/<期号>/vision_extract.json`: 多图 Vision 汇总 JSON。
- `ai-workflow/cache/<期号>/brief.md`: 多资料事实 brief。
- `ai-workflow/cache/<期号>/brief_scope.json`: 按决策记录裁剪后的结构化范围。
- `ai-workflow/cache/<期号>/qwen3-prompt.md`: 本次交叉分析发送给 Qwen3 的完整提示词。
- `ai-workflow/cache/<期号>/qwen3-raw.json`: Qwen3 原始响应和元数据。
- `ai-workflow/output/<期号>/当期分析.md`: 最终多资料交叉分析。
