"""n-gram 指纹单元测试。"""

from engine.fingerprint.ngram import ngram_set, containment_score, iter_ngrams


def test_iter_ngrams_window():
    grams = list(iter_ngrams("abcd", 2))
    assert grams == ["ab", "bc", "cd"]


def test_ngram_set_multiwindow():
    grams = ngram_set("你好世界")
    assert "你好" in grams
    assert "你好世" in grams
    assert "你好世界" in grams


def test_containment_score_full():
    a = ngram_set("机器学习")
    b = ngram_set("机器学习")
    assert containment_score(a, b) == 1.0


def test_containment_score_partial():
    a = ngram_set("机器学习算法")
    b = ngram_set("机器学习应用")
    score = containment_score(a, b)
    assert 0.0 < score < 1.0


def test_containment_empty():
    assert containment_score(set(), ngram_set("abc")) == 0.0
