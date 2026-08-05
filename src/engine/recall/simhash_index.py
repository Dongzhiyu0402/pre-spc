"""SimHash 倒排/分段索引 + 汉明距离召回候选文档。

结构：将 64 位 simhash 拆成 8 段（每段 8 位）建立倒排表（比 4x16 更细粒度，
对短查询 vs 长文档召回更友好）。查询时在每段桶内做汉明距离过滤，合并候选，
按距离排序取 top_k。

小语料回退：当候选为空且语料规模小于 FALLBACK_SCAN_LIMIT 时，直接全量扫描
（保证 demo 语料与小型内部基准的确定性召回，无假阴性）。
确定性：同输入同输出。
"""

from dataclasses import dataclass, field

from engine.fingerprint.simhash import hamming_distance, simhash
from engine.fingerprint.ngram import ngram_set, containment_score

NUM_BANDS = 8
BAND_BITS = 8
_BAND_MASK = (1 << BAND_BITS) - 1

# 全量扫描回退上限：语料小于该数量时允许直接扫描（MVP 语料规模内安全）
FALLBACK_SCAN_LIMIT = 10000


@dataclass
class CorpusDoc:
    """语料库文档条目。"""

    doc_id: str
    text: str
    simhash_value: int
    ngram_grams: set[str] = field(default_factory=set)

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "text": self.text,
            "simhash_value": self.simhash_value,
            "ngram_grams": sorted(self.ngram_grams),
        }


class SimhashIndex:
    """基于 SimHash 段的候选召回索引。"""

    def __init__(self) -> None:
        self._bands: list[dict[int, list[CorpusDoc]]] = [{} for _ in range(NUM_BANDS)]
        self._docs: list[CorpusDoc] = []

    def add(self, doc: CorpusDoc) -> None:
        self._docs.append(doc)
        for band in range(NUM_BANDS):
            key = self._band_value(doc.simhash_value, band)
            self._bands[band].setdefault(key, []).append(doc)

    @staticmethod
    def _band_value(fp: int, band: int) -> int:
        return (fp >> (band * BAND_BITS)) & _BAND_MASK

    def _band_recall(self, query_simhash: int) -> dict[int, CorpusDoc]:
        candidates: dict[int, CorpusDoc] = {}
        for band in range(NUM_BANDS):
            key = self._band_value(query_simhash, band)
            for doc in self._bands[band].get(key, []):
                candidates[id(doc)] = doc
        return candidates

    def _scan_recall(self, query_grams: set[str], top_k: int, min_score: float = 0.02) -> list[CorpusDoc]:
        """全量扫描（小语料回退），按 n-gram 包含度取前 top_k。

        SimHash 汉明距离对"短查询 vs 长文档"不敏感，回退改用包含度——
        这正是精算阶段的主判据，保证无假阴性（确定性）。
        """
        scored = []
        for doc in self._docs:
            if not doc.ngram_grams:
                continue
            score = containment_score(query_grams, doc.ngram_grams)
            if score >= min_score:
                scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]

    def recall(
        self,
        query_simhash: int,
        top_k: int = 20,
        max_distance: int = 24,
        query_grams: set[str] | None = None,
    ) -> list[CorpusDoc]:
        """召回候选：至少一段相同的文档，再按汉明距离排序。

        无候选且语料规模小于 FALLBACK_SCAN_LIMIT 时，若有 query_grams 则
        按 n-gram 包含度全量扫描兜底（防假阴性）。
        """
        candidates = self._band_recall(query_simhash)
        scored = []
        for doc in candidates.values():
            dist = hamming_distance(query_simhash, doc.simhash_value)
            if dist <= max_distance:
                scored.append((dist, doc))
        scored.sort(key=lambda x: x[0])
        if scored:
            return [doc for _, doc in scored[:top_k]]
        # 无候选 + 小语料 -> 包含度全量扫描兜底
        if query_grams is not None and len(self._docs) <= FALLBACK_SCAN_LIMIT:
            return self._scan_recall(query_grams, top_k)
        return []

    def build_from_texts(self, docs: list[tuple[str, str]]) -> None:
        """批量构建：docs = [(doc_id, text), ...]。"""
        for doc_id, text in docs:
            if not text.strip():
                continue
            self.add(
                CorpusDoc(
                    doc_id=doc_id,
                    text=text,
                    simhash_value=simhash(text),
                    ngram_grams=ngram_set(text),
                )
            )

    def size(self) -> int:
        return len(self._docs)

    def to_dict(self) -> list[dict]:
        return [d.to_dict() for d in self._docs]
