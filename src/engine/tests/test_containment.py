"""包含度与片段聚合单元测试。"""

from engine.fingerprint.ngram import ngram_set
from engine.fingerprint.simhash import simhash, hamming_distance
from engine.recall.simhash_index import SimhashIndex, CorpusDoc
from engine.scoring.segment_agg import aggregate_segments
from engine.scoring.longest_match import longest_matched_runs


def _doc(doc_id: str, text: str) -> CorpusDoc:
    return CorpusDoc(
        doc_id=doc_id,
        text=text,
        simhash_value=simhash(text),
        ngram_grams=ngram_set(text),
    )


def test_simhash_deterministic():
    fp1 = simhash("机器学习是人工智能的重要分支")
    fp2 = simhash("机器学习是人工智能的重要分支")
    assert fp1 == fp2


def test_simhash_distance_similar():
    a = simhash("自然语言处理技术在文本分析中广泛应用")
    b = simhash("自然语言处理技术在文本分析中广泛应用")
    c = simhash("今天天气很好适合出门散步运动")
    assert hamming_distance(a, b) <= 4
    assert hamming_distance(a, c) > hamming_distance(a, b)


def test_recall_returns_similar():
    index = SimhashIndex()
    target = _doc("t1", "基于深度学习的文本相似度计算方法研究")
    index.add(target)
    cands = index.recall(simhash("基于深度学习的文本相似度计算方法研究"), top_k=5, max_distance=24)
    assert any(c.doc_id == "t1" for c in cands)


def test_aggregate_high_repeat():
    source = "随着信息技术的快速发展教育信息化成为高等教育改革的重要方向之一。"
    query = source + "这段是完全原创的新内容。"
    index = SimhashIndex()
    index.add(_doc("s1", source))
    cands = index.recall(simhash(query), top_k=5, max_distance=24)
    agg = aggregate_segments(query, cands)
    assert agg.raw_score > 30
    assert any(s.highlight_type in ("high", "mid") for s in agg.segments)


def test_longest_match_runs():
    source = "城市交通拥堵问题日益突出制约城市可持续发展"
    query = "城市交通拥堵问题日益突出制约城市可持续发展新增内容"
    cand = _doc("c1", source)
    runs = longest_matched_runs(query, cand.ngram_grams, min_run=8)
    assert any(end - start >= 8 for start, end in runs)
