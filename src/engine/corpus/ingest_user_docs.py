"""用户脱敏文档入库（授权后）。

MVP 占位：仅提供接口签名与最小实现，正式接入由后端 worker 调 engine 层。
"""

from engine.cleaning.text_cleaner import clean_text
from engine.corpus.opencc_norm import to_simplified


def ingest_user_doc(doc_id: str, raw_text: str) -> str:
    """清洗用户文档并返回可入库文本（脱敏后）。

    仅返回清洗文本，实际入库由上层负责（Web 端需用户授权）。
    """
    return clean_text(to_simplified(raw_text))
