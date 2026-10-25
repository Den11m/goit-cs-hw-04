"""Спільні функції для пошуку ключових слів у текстових файлах."""

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


def collect_files(directory: str | Path, pattern: str = "*.txt") -> list[Path]:
    """Повертає відсортований список файлів у директорії за шаблоном."""
    directory = Path(directory)
    if not directory.is_dir():
        raise NotADirectoryError(f"Директорію не знайдено: {directory}")
    return sorted(p for p in directory.glob(pattern) if p.is_file())


def split_into_chunks(items: list, n: int) -> list[list]:
    """Розподіляє елементи між n частинами (round-robin), порожні частини відкидає."""
    n = max(1, n)
    return [chunk for chunk in (items[i::n] for i in range(n)) if chunk]


def read_file(path: str | Path) -> str | None:
    """Читає файл, повертає None і логує помилку, якщо читання неможливе."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error("Файл не знайдено: %s", path)
    except PermissionError:
        logger.error("Немає доступу до файлу: %s", path)
    except IsADirectoryError:
        logger.error("Шлях є директорією, а не файлом: %s", path)
    except UnicodeDecodeError:
        logger.error("Не вдалося декодувати файл як UTF-8: %s", path)
    except OSError as e:
        logger.error("Помилка читання файлу %s: %s", path, e)
    return None


def build_patterns(keywords: list[str]) -> dict[str, re.Pattern]:
    """Компілює регулярні вирази для пошуку цілих слів без урахування регістру."""
    return {kw: re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE) for kw in keywords}


def search_in_files(files: list[str | Path], keywords: list[str]) -> dict[str, list[str]]:
    """Шукає ключові слова у списку файлів.

    Повертає словник {ключове слово: [шляхи файлів, де його знайдено]}.
    """
    patterns = build_patterns(keywords)
    results: dict[str, list[str]] = {kw: [] for kw in keywords}

    for path in files:
        text = read_file(path)
        if text is None:
            continue
        for kw, pattern in patterns.items():
            if pattern.search(text):
                results[kw].append(str(path))

    return results


def merge_results(target: dict[str, list[str]], source: dict[str, list[str]]) -> None:
    """Додає результати source до target."""
    for kw, paths in source.items():
        target.setdefault(kw, []).extend(paths)


def print_results(title: str, results: dict[str, list[str]], elapsed: float) -> None:
    """Виводить результати пошуку та час виконання."""
    print(f"\n=== {title} ===")
    for kw, paths in results.items():
        found = ", ".join(Path(p).name for p in paths) if paths else "не знайдено"
        print(f"  {kw!r}: {found}")
    print(f"Час виконання: {elapsed:.4f} с")
