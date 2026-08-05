"""清洗与分段单元测试。"""

from engine.cleaning.text_cleaner import clean_text
from engine.cleaning.section_splitter import split_sections


def test_clean_removes_whitespace():
    assert clean_text("  你好  世界  ") == "你好 世界"


def test_clean_strips_punct():
    result = clean_text("你好，世界！")
    assert "，" not in result
    assert "！" not in result


def test_clean_drops_reference_tail():
    text = "正文内容。\n参考文献\n[1] 张三. 某文献. 2020."
    result = clean_text(text)
    assert "参考文献" not in result
    assert "正文内容" in result


def test_clean_removes_page_noise():
    text = "第 3 页\n正文\n第 4 页"
    result = clean_text(text)
    assert "第 3 页" not in result


def test_split_sections():
    text = "摘要\n这是摘要内容。\n结论\n这是结论内容。"
    sections = split_sections(text)
    names = [name for name, _ in sections]
    assert "摘要" in names
    assert "结论" in names


def test_split_sections_body_fallback():
    sections = split_sections("没有任何标题的普通文本")
    assert sections == [("body", "没有任何标题的普通文本")]
