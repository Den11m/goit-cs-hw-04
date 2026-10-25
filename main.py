"""Порівняння багатопотокового та багатопроцесорного пошуку ключових слів у файлах.

Приклад запуску:
    python main.py --dir data --keywords python thread process queue lock --workers 4
"""

import argparse
import logging
import sys

import multiprocessing_search
import threading_search
from search_utils import collect_files, print_results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Паралельний пошук ключових слів у текстових файлах")
    parser.add_argument("--dir", default="data", help="директорія з .txt файлами (за замовчуванням: data)")
    parser.add_argument(
        "--keywords",
        nargs="+",
        default=["python", "thread", "process", "queue", "lock", "missing"],
        help="ключові слова для пошуку",
    )
    parser.add_argument("--workers", type=int, default=4, help="кількість потоків/процесів")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(processName)s] %(message)s")
    args = parse_args()

    try:
        files = collect_files(args.dir)
    except NotADirectoryError as e:
        logging.error(e)
        sys.exit(1)

    if not files:
        logging.error("У директорії %s немає .txt файлів", args.dir)
        sys.exit(1)

    print(f"Файлів: {len(files)}, ключові слова: {args.keywords}, воркерів: {args.workers}")

    thread_results, thread_time = threading_search.run(files, args.keywords, args.workers)
    print_results("threading", thread_results, thread_time)

    process_results, process_time = multiprocessing_search.run(files, args.keywords, args.workers)
    print_results("multiprocessing", process_results, process_time)

    print(f"\nРезультати збігаються: {thread_results == process_results}")


if __name__ == "__main__":
    main()
