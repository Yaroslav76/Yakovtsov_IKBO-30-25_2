"""Инструмент визуализации графа зависимостей (вариант 30, Maven).

Запуск: python3 src/main.py config.json [--stage N]
"""
import argparse
import sys

import stages
from config import ConfigError, load_config

STATUS_CONFIG = 2
STATUS_DATA = 1


def parse_args(argv=None):
    """Разбирает параметры командной строки."""
    last = max(stages.HANDLERS)
    parser = argparse.ArgumentParser(
        description="Граф зависимостей пакетов Maven")
    parser.add_argument("config", help="путь к конфигурационному JSON")
    parser.add_argument("--stage", type=int, default=last,
                        choices=sorted(stages.HANDLERS),
                        help="номер этапа, вывод которого показать")
    return parser.parse_args(argv)


def main(argv=None):
    """Точка входа: читает конфигурацию и запускает обработчик этапа."""
    args = parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if not stream.isatty():
            stream.reconfigure(encoding="utf-8")
    try:
        return stages.HANDLERS[args.stage](load_config(args.config))
    except ConfigError as e:
        for message in e.errors:
            print(f"Ошибка конфигурации: {message}", file=sys.stderr)
        return STATUS_CONFIG
    except stages.DATA_ERRORS as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return STATUS_DATA


if __name__ == "__main__":
    sys.exit(main())
