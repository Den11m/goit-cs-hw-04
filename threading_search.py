"""Багатопотокова версія пошуку ключових слів (threading)."""

import logging
import threading
import time
from pathlib import Path

from search_utils import merge_results, search_in_files, split_into_chunks

logger = logging.getLogger(__name__)


def threaded_search(
    files: list[str | Path], keywords: list[str], num_threads: int = 4
) -> dict[str, list[str]]:
    """Розподіляє файли між потоками і повертає {ключове слово: [шляхи файлів]}."""
    results: dict[str, list[str]] = {kw: [] for kw in keywords}
    lock = threading.Lock()

    def worker(chunk: list[str | Path]) -> None:
        try:
            partial = search_in_files(chunk, keywords)
        except Exception:
            logger.exception("Помилка в потоці %s", threading.current_thread().name)
            return
        with lock:
            merge_results(results, partial)

    threads = [
        threading.Thread(target=worker, args=(chunk,), name=f"Thread-{i}")
        for i, chunk in enumerate(split_into_chunks(list(files), num_threads))
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for paths in results.values():
        paths.sort()
    return results


def run(files: list[str | Path], keywords: list[str], num_threads: int = 4):
    """Запускає пошук і вимірює час виконання."""
    start = time.perf_counter()
    results = threaded_search(files, keywords, num_threads)
    elapsed = time.perf_counter() - start
    return results, elapsed
