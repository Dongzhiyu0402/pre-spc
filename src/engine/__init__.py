"""预查重引擎（纯 Python，双端共用）。

统一入口：run_check(text, plan_params) -> EngineResult
不依赖任何 Web 框架 / HTTP 对象，保证桌面端离线可用（AC-16）。
"""

from engine.cleaning.text_cleaner import clean_text
from engine.cleaning.section_splitter import split_sections
from engine.cleaning.doc_extractor import extract_text_from_bytes
from engine.corpus.build import build_default_corpus
from engine.pipeline import run_check, EngineResult

__all__ = [
    "clean_text",
    "split_sections",
    "extract_text_from_bytes",
    "run_check",
    "EngineResult",
    "build_default_corpus",
]

__version__ = "0.1.0"
