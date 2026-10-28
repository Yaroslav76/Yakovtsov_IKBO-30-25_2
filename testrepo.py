"""Тестовый репозиторий: файл с описанием графа зависимостей.

Формат: по строке на пакет, 'A: B C' - пакет A зависит от B и C.
Имена - большие латинские буквы. Пустые строки и строки с решёткой
в начале пропускаются.
"""
import re

NAME = re.compile(r"^[A-Z]+$")
COMMENT = "#"


class TestRepoError(Exception):
    """Ошибка чтения или разбора файла тестового репозитория."""


def _parse_line(number, line):
    """Разбирает строку 'A: B C'; возвращает (имя, список зависимостей)."""
    name, separator, rest = line.partition(":")
    name = name.strip()
    if not separator or not NAME.match(name):
        raise TestRepoError(
            f"строка {number}: ожидается 'ИМЯ: ЗАВИСИМОСТИ', имена - "
            "большие латинские буквы")
    deps = rest.split()
    bad = [dep for dep in deps if not NAME.match(dep)]
    if bad:
        raise TestRepoError(
            f"строка {number}: недопустимое имя пакета '{bad[0]}'")
    return name, list(dict.fromkeys(deps))


def parse_graph(text):
    """Разбирает текст файла; возвращает {пакет: [зависимости]}."""
    graph = {}
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(COMMENT):
            continue
        name, deps = _parse_line(number, line)
        if name in graph:
            raise TestRepoError(
                f"строка {number}: пакет '{name}' описан повторно")
        graph[name] = deps
    for deps in list(graph.values()):
        for dep in deps:
            graph.setdefault(dep, [])
    return graph


def load_graph(path):
    """Читает файл тестового репозитория и разбирает его."""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError) as e:
        raise TestRepoError(f"не удалось прочитать '{path}': {e}")
    return parse_graph(text)
