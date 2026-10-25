"""Багатопроцесорна версія пошуку ключових слів (multiprocessing + Queue)."""

import logging
import multiprocessing as mp
import queue
import time
from pathlib import Path

from search_utils import merge_results, search_in_files, split_into_chunks

logger = logging.getLogger(__name__)

RESULT_TIMEOUT = 30  # секунд очікування результату від одного процесу


def worker(chunk: list[str], keywords: list[str], result_queue: mp.Queue) -> None:
    """Обробляє свою частину файлів і кладе результат у чергу."""
    try:
        result_queue.put(("ok", search_in_files(chunk, keywords)))
    except Exception as e:
        result_queue.put(("error", f"{type(e).__name__}: {e}"))


def multiprocess_search(
    files: list[str | Path], keywords: list[str], num_processes: int = 4
) -> dict[str, list[str]]:
    """Розподіляє файли між процесами і повертає {ключове слово: [шляхи файлів]}."""
    results: dict[str, list[str]] = {kw: [] for kw in keywords}
    result_queue: mp.Queue = mp.Queue()

    chunks = split_into_chunks([str(f) for f in files], num_processes)
    processes = [
        mp.Process(target=worker, args=(chunk, keywords, result_queue), name=f"Process-{i}")
        for i, chunk in enumerate(chunks)
    ]
    for p in processes:
        p.start()

    # Забираємо результати з черги до join(), щоб уникнути дедлоку на заповненій черзі
    for _ in processes:
        try:
            status, payload = result_queue.get(timeout=RESULT_TIMEOUT)
        except queue.Empty:
            logger.error("Не отримано результат від одного з процесів")
            continue
        if status == "ok":
            merge_results(results, payload)
        else:
            logger.error("Помилка в процесі: %s", payload)

    for p in processes:
        p.join()
        if p.exitcode != 0:
            logger.error("%s завершився з кодом %s", p.name, p.exitcode)

    for paths in results.values():
        paths.sort()
    return results


def run(files: list[str | Path], keywords: list[str], num_processes: int = 4):
    """Запускає пошук і вимірює час виконання."""
    start = time.perf_counter()
    results = multiprocess_search(files, keywords, num_processes)
    elapsed = time.perf_counter() - start
    return results, elapsed
