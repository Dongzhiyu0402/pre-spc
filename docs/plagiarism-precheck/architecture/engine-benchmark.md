# 预查重项目 M2 引擎基准测试方案 v1.0

> 生成日期：2026-08-05
> 依据：Spec-预查重项目-v1.0.md（AC-01~16）+ Phase1 架构文档（算法选型：n-gram 主判据 + SimHash 召回 + 校准）
> 用途：M2 门禁（在已知真值样本上相关性达标）唯一测试依据
> 前置：本方案假定已实现 `engine/` 最小流水线（cleaning → fingerprint → recall → scoring）

---

## 1. 测试目标与门禁

| 目标 | 指标 | M2 门禁阈值 |
|------|------|-------------|
| 引擎对已知真值样本的预估精度 | MAE（校准前 raw_score vs 真值） | ≤ 15%（校准前可放宽，校准后收敛） |
| 预估与真值的相关性 | Spearman 相关系数 | ≥ 0.6 |
| 片段查全率（真值重复片段是否被引擎标出） | Recall@片段 | ≥ 0.7 |
| 性能 | 1 万字文档处理耗时 | ≤ 30 秒（AC-01） |

> 说明：MAE 目标收敛 5% 是校准层（M4）目标；M2 只验证"引擎排序相关性 + 片段查全"，绝对数值由校准兜底。UI 呈现预估区间，不承诺与知网一致（Spec §3）。

---

## 2. 测试集构造（人工标注样本 ≥30 条）

### 2.1 样本构成（建议 30~50 条，覆盖高中低相似度分布）

| 分组 | 数量 | 构造方式 | 标注真值 |
|------|------|----------|----------|
| A 组：复制粘贴 | 10~15 | 从种子语料/公开论文片段整段复制拼接成"论文" | 人工标注：逐片段标记"重复/改写/引用/原创"，计算真值重复率 |
| B 组：轻度改写 | 8~10 | 对来源文本做同义词替换/语序调整/句子合并 | 同上 |
| C 组：原创 | 5~8 | 完全原创文本（含常见学术套话） | 真值 ≈ 低重复（<10%） |
| D 组：真实回传 | 5~10 | 试点用户真实论文 + 真实平台报告（脱敏） | 平台真实查重率（real_rate） |

### 2.2 标注格式（`testsets/labeled.jsonl`）

每行一条 JSON：
```json
{
  "sample_id": "A-001",
  "group": "A",
  "source_text_path": "corpus/sources/source_001.txt",
  "doc_path": "testsets/docs/a_001.txt",
  "platform": "cnki",
  "paper_type": "undergrad",
  "true_rate": 42.5,
  "segments": [
    {"start_offset": 120, "end_offset": 340, "label": "duplicate", "source": "source_001"},
    {"start_offset": 500, "end_offset": 620, "label": "rewrite", "source": "source_001"}
  ]
}
```

### 2.3 标注规则

- 真值重复率 = 被标记为 `duplicate` 的字符数 / 总字符数 × 100（与平台"重复率"口径一致）。
- `rewrite`（改写）不记入重复率真值，但用于评估"是否被召回为 mid"。
- 每条样本至少 2 人独立标注，不一致处第三人仲裁（标注质量门禁）。
- 真实回传样本需用户授权脱敏；无真实样本时 D 组可暂缺，但门禁以 A/B/C 组为准。

---

## 3. 指标定义

| 指标 | 定义 | 计算方式 |
|------|------|----------|
| MAE | 平均绝对误差 | `mean(|predicted_rate - true_rate|)` |
| Spearman ρ | 排序相关性 | `scipy.stats.spearmanr(predicted, true)` |
| 片段查全率 Recall | 真值重复片段被引擎命中比例 | 以 offset 区间重叠 ≥50% 判定命中；`TP / (TP+FN)` |
| 片段精确率 Precision | 引擎标出的片段中真值占比 | `TP / (TP+FP)` |
| p95 耗时 | 引擎单文档处理时间 | 计时 `run_check` 全流程 |

> 防沉默逻辑错误：指标计算必须写进测试用例（`test_metrics.py`），不允许"肉眼比对"人工判断是否达标。

---

## 4. 种子语料库构建步骤（THUCNews + 中文维基）

> 语料仅内部基准，不得对外宣称"学术比对库"（Spec §10）。版权：THUCNews 免费供研究者使用、维基 CC BY-SA 4.0，均不得再分发为商业比对库。

### 4.1 THUCNews（约 74~84 万篇新闻，1.45~2.19GB）

```bash
# 1) 下载（需在 thuctc.thunlp.org 登记个人信息）
#    或使用 HF 镜像数据集（thunlp/THUCNews 或社区镜像）
# 2) 抽样子集：随机抽样 5 万篇（控制构建时间与索引体积，MVP 语料规模足够）
python -m engine.corpus.build --source thucnews --input /data/thucnews --sample 50000 \
  --output /data/corpus/thucnews_50k
```

### 4.2 中文维基 dump（约 150 万词条，2.2GB JSON）

```bash
# 1) 下载 zhwiki dump（dumps.wikimedia.org/zhwiki/latest/zhwiki-latest-pages-articles.xml.bz2）
# 2) WikiExtractor 抽取纯文本
wikiextractor zhwiki-latest-pages-articles.xml.bz2 -o /data/wiki_extracted --json --process 4
# 3) 简繁归一（OpenCC：t2s）+ 清洗 + 指纹入库
python -m engine.corpus.build --source wiki --input /data/wiki_extracted \
  --output /data/corpus/wiki_zh --opencc t2s
```

### 4.3 统一建库（指纹索引）

```bash
# 对 THUCNews 子集 + 维基合并去重，生成 SimHash/MinHash 索引快照
python -m engine.corpus.build --merge \
  --inputs /data/corpus/thucnews_50k,/data/corpus/wiki_zh \
  --output engine/models/corpus_index --dedup minhash
```

### 4.4 语料库清单

| 语料 | 用途 | 版权 | 存储 |
|------|------|------|------|
| THUCNews 5 万篇 | 新闻类重复检测基准 + 种子库 | 研究者免费使用 | /data/corpus/thucnews_50k |
| 中文维基 150 万词条 | 百科类重复检测基准 + 种子库 | CC BY-SA 4.0 | /data/corpus/wiki_zh |
| 用户脱敏文档（可选） | 补充论文分布语料 | 用户授权 | 服务端加密存储，30 天清理 |

---

## 5. 基准命令

### 5.1 跑基准

```bash
# 全量基准（30+ 标注样本）
python -m engine.benchmark.run \
  --testset testsets/labeled.jsonl \
  --corpus-index engine/models/corpus_index \
  --plan cnki_sim \
  --output reports/benchmark_cnki.json

# 分平台基准（校准分桶用）
python -m engine.benchmark.run --testset testsets/labeled.jsonl --plan vip_sim --output reports/benchmark_vip.json
python -m engine.benchmark.run --testset testsets/labeled.jsonl --plan wanfang_sim --output reports/benchmark_wanfang.json
```

### 5.2 输出报告（`reports/benchmark_*.json`）

```json
{
  "plan_code": "cnki_sim",
  "sample_count": 32,
  "mae_raw": 12.4,
  "spearman_raw": 0.71,
  "recall_dup": 0.78,
  "precision_dup": 0.65,
  "p95_ms": 8200,
  "samples": [{"sample_id": "A-001", "true_rate": 42.5, "raw_score": 38.1, "hit": true}]
}
```

### 5.3 门禁判定

```bash
# 门禁脚本：全部指标达标返回 0，否则非 0（接入 CI）
python -m engine.benchmark.gate \
  --input reports/benchmark_cnki.json \
  --mae-max 15 --spearman-min 0.6 --recall-min 0.7 --p95-max 30000
```

---

## 6. 已知限制与边界（必须记录进基准报告）

1. **绝对数值与知网不可比**：种子语料是新闻/百科，非学术论文库。raw_score 只用于排序与校准特征，UI 呈现预估区间（Spec §3/§10）。
2. **改写召回上限**：n-gram 主判据对同义改写不敏感，B 组（改写）预期 recall 较低属正常；改写的片段应命中为 `mid`（中重复橙）而非 `high`。
3. **来源提示有限**：新闻/百科语料来源非论文，报告来源提示措辞需与"非学术比对库"切割（Spec §10）。
4. **D 组样本依赖试点启动**：M2 阶段允许 D 组为空，M4 校准训练以 D 组为主要增量。
5. **确定性**：SimHash 召回 + n-gram 精算应为确定性输出（同输入同输出），基准报告须标注引擎版本 + 语料库快照版本，供校准样本元数据对齐（校准模型错配防护）。

---

## 7. M2 完成定义（门禁）

- [ ] 测试集 ≥30 条标注样本（A/B/C 组必含，D 组可选），标注仲裁记录完整
- [ ] 种子语料构建完成（THUCNews 子集 + 维基，指纹索引可查询）
- [ ] 基准命令可复现，输出报告含全部指标
- [ ] 门禁判定通过：MAE ≤15、Spearman ≥0.6、Recall ≥0.7、p95 ≤30s
- [ ] 基准报告含"已知限制与边界"章节（§6 逐条确认）
- [ ] 引擎版本 + 语料库快照版本已记录（供校准元数据对齐）

---

*变更记录：v1.0 创建（2026-08-05）*
