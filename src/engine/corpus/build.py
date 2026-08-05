"""种子语料构建流水线（THUCNews/维基/内置 demo -> 指纹 -> 入库）。

- 无网络时使用内置 demo 语料跑通基准（team-lead 要求）。
- 语料仅内部基准，不得对外宣称"学术比对库"（Spec §10）。
"""

import json
import os

from engine.cleaning.text_cleaner import clean_text
from engine.corpus.opencc_norm import to_simplified
from engine.fingerprint.minhash import jaccard_estimate, minhash_signature
from engine.recall.simhash_index import SimhashIndex, CorpusDoc

DEMO_CORPUS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "demo_corpus")
DEFAULT_INDEX_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "corpus_index")

INDEX_FILENAME = "corpus_index.json"
META_FILENAME = "meta.json"

_MINHASH_TOP_N = 3  # 去重时每个文档比较的前 N 个候选（简化）
_DEDUP_JACCARD = 0.9  # 超过该相似度视为重复


def _load_texts_from_dir(directory: str) -> list[tuple[str, str]]:
    """加载目录下所有 .txt 文件 -> [(doc_id, cleaned_text)]。"""
    docs: list[tuple[str, str]] = []
    if not os.path.isdir(directory):
        return docs
    for fname in sorted(os.listdir(directory)):
        if not fname.endswith(".txt"):
            continue
        path = os.path.join(directory, fname)
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
        cleaned = clean_text(to_simplified(raw))
        if cleaned.strip():
            docs.append((fname, cleaned))
    return docs


def dedup_docs(docs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """MinHash 去重（近似 Jaccard 高则保留首个）。"""
    if len(docs) <= 1:
        return docs
    sigs = [minhash_signature(text) for _, text in docs]
    kept: list[int] = []
    for i in range(len(docs)):
        dup = False
        for j in kept:
            if jaccard_estimate(sigs[i], sigs[j]) >= _DEDUP_JACCARD:
                dup = True
                break
        if not dup:
            kept.append(i)
    return [docs[i] for i in kept]


def build_index(docs: list[tuple[str, str]], dedup: bool = True) -> SimhashIndex:
    """从 (doc_id, text) 构建 SimHash 索引。"""
    if dedup:
        docs = dedup_docs(docs)
    index = SimhashIndex()
    for doc_id, text in docs:
        index.add(
            CorpusDoc(
                doc_id=doc_id,
                text=text,
                simhash_value=_simhash_of(text),
                ngram_grams=_ngrams_of(text),
            )
        )
    return index


def _simhash_of(text: str) -> int:
    from engine.fingerprint.simhash import simhash

    return simhash(text)


def _ngrams_of(text: str) -> set[str]:
    from engine.fingerprint.ngram import ngram_set

    return ngram_set(text)


def build_default_corpus(index_dir: str = DEFAULT_INDEX_DIR, force: bool = False) -> SimhashIndex:
    """构建内置 demo 语料索引；已存在且非 force 时直接加载。"""
    index_path = os.path.join(index_dir, INDEX_FILENAME)
    if os.path.exists(index_path) and not force:
        loaded = load_index(index_dir)
        if loaded.size() > 0:
            return loaded
    docs = _load_texts_from_dir(DEMO_CORPUS_DIR)
    index = build_index(docs)
    save_index(index, index_dir, source="demo")
    return index


def save_index(index: SimhashIndex, index_dir: str, source: str = "demo") -> str:
    """保存索引到磁盘（JSON）。"""
    os.makedirs(index_dir, exist_ok=True)
    payload = {"docs": index.to_dict()}
    with open(os.path.join(index_dir, INDEX_FILENAME), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False)
    meta = {"source": source, "doc_count": index.size(), "version": "0.1.0"}
    with open(os.path.join(index_dir, META_FILENAME), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
    return index_dir


def load_index(index_dir: str = DEFAULT_INDEX_DIR) -> SimhashIndex:
    """从磁盘加载索引。缺失或损坏时回退内置 demo。"""
    index_path = os.path.join(index_dir, INDEX_FILENAME)
    if not os.path.exists(index_path):
        return build_default_corpus(index_dir)
    try:
        with open(index_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        index = SimhashIndex()
        for doc in payload.get("docs", []):
            grams = set(doc.get("ngram_grams", []))
            if not grams:
                grams = _ngrams_of(doc.get("text", ""))
            index.add(
                CorpusDoc(
                    doc_id=doc.get("doc_id", ""),
                    text=doc.get("text", ""),
                    simhash_value=int(doc.get("simhash_value", 0)),
                    ngram_grams=grams,
                )
            )
        return index
    except (json.JSONDecodeError, KeyError, ValueError):
        return build_default_corpus(index_dir, force=True)


def load_or_build_index(index_dir: str = DEFAULT_INDEX_DIR) -> SimhashIndex:
    """加载索引；不存在则构建内置 demo 索引。"""
    return load_index(index_dir)


def main() -> None:  # pragma: no cover
    """CLI：python -m engine.corpus.build --source demo|dir --input PATH --output DIR"""
    import argparse

    parser = argparse.ArgumentParser(description="种子语料构建")
    parser.add_argument("--source", default="demo", help="demo | 目录路径")
    parser.add_argument("--input", default=None, help="语料目录（source=demo 时忽略）")
    parser.add_argument("--output", default=DEFAULT_INDEX_DIR, help="索引输出目录")
    parser.add_argument("--dedup", action="store_true", default=True, help="MinHash 去重")
    args = parser.parse_args()

    if args.source == "demo":
        docs = _load_texts_from_dir(DEMO_CORPUS_DIR)
    else:
        docs = _load_texts_from_dir(args.input)
    index = build_index(docs, dedup=args.dedup)
    save_index(index, args.output, source=args.source)
    print(f"corpus built: {index.size()} docs -> {args.output}")


if __name__ == "__main__":  # pragma: no cover
    main()
