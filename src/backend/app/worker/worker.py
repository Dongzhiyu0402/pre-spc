"""RQ worker 入口：独立进程消费查重/校准任务。

运行：python -m app.worker.worker
"""

import os
import sys

# 保证 engine 可导入（backend 与 engine 同级于 src/）
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import redis
from rq import Worker, Queue

from app.config import settings


def main() -> None:  # pragma: no cover
    conn = redis.from_url(settings.redis_url)
    queue = Queue(settings.rq_queue_name, connection=conn)
    worker = Worker([queue], connection=conn)
    worker.work()


if __name__ == "__main__":  # pragma: no cover
    main()
