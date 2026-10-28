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