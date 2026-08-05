"""文档抽取：docx/txt/md/pdf -> 纯文本。

设计约束：
- 引擎不强制依赖第三方库（桌面端离线可用 AC-16）。
- docx 用 zipfile + XML 解析（stdlib），不依赖 python-docx。
- pdf 优先 PyMuPDF（fitz），未安装时抛 DocExtractError 并给出清晰提示。
"""

import io
import re
import zipfile
from xml.etree import ElementTree as ET

SUPPORTED_EXT = {".txt", ".md", ".docx", ".pdf"}


class DocExtractError(Exception):
    """文档解析失败。"""


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8", "gb18030", "gbk", "utf-16"):
        try:
            return data.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    raise DocExtractError("无法识别文本编码（尝试 utf-8/gb18030/gbk）")


def _extract_docx(data: bytes) -> str:
    """从 .docx 提取纯文本（stdlib zipfile + XML）。"""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            xml_bytes = zf.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile) as exc:
        raise DocExtractError(f"docx 文件损坏: {exc}") from exc
    root = ET.fromstring(xml_bytes)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for para in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
        texts = [
            node.text or ""
            for node in para.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")
        ]
        paragraphs.append("".join(texts))
    return "\n".join(paragraphs)


def _extract_pdf(data: bytes) -> str:
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:  # pragma: no cover
        raise DocExtractError("pdf 解析需要 PyMuPDF，请安装 pymupdf") from exc
    doc = fitz.open(stream=data, filetype="pdf")
    pages = [page.get_text("text") for page in doc]
    doc.close()
    return "\n".join(pages)


def extract_text_from_bytes(data: bytes, filename: str) -> str:
    """按扩展名抽取文本。返回清洗前原始文本。"""
    ext = re.search(r"\.([a-zA-Z0-9]+)$", filename)
    ext = ("." + ext.group(1).lower()) if ext else ""
    if ext not in SUPPORTED_EXT:
        raise DocExtractError(f"不支持的文件类型: {ext or '未知'}，仅支持 txt/md/docx/pdf")
    if ext in (".txt", ".md"):
        return _decode_text(data)
    if ext == ".docx":
        return _extract_docx(data)
    if ext == ".pdf":
        return _extract_pdf(data)
    raise DocExtractError(f"不支持的文件类型: {ext}")
