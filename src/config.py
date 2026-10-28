"""Загрузка и проверка конфигурационного файла в формате JSON."""
import json
import os
import re
from dataclasses import asdict, dataclass

MIN_DEPTH = 0
REQUIRED = ("package", "repository")
DEFAULTS = {
    "version": "",
    "test_mode": False,
    "ascii_tree": False,
    "max_depth": 3,
    "reverse": False,
}
MAVEN_NAME = re.compile(r"^[A-Za-z0-9_.\-]+:[A-Za-z0-9_.\-]+$")
TEST_NAME = re.compile(r"^[A-Z]+$")
VERSION = re.compile(r"^[A-Za-z0-9_.+\-]+$")
URL_SCHEMES = ("http://", "https://", "file://")


class ConfigError(Exception):
    """Ошибки конфигурации: хранит список сообщений."""

    def __init__(self, errors):
        """errors - список текстов ошибок."""
        super().__init__("; ".join(errors))
        self.errors = list(errors)


@dataclass(frozen=True)
class Config:
    """Проверенные параметры приложения."""

    package: str
    version: str
    repository: str
    test_mode: bool
    ascii_tree: bool
    max_depth: int
    reverse: bool

    def pairs(self):
        """Параметры как список пар (ключ, значение)."""
        return list(asdict(self).items())


def _read_json(path):
    """Читает JSON-объект из файла; при ошибке бросает ConfigError."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise ConfigError([f"файл конфигурации не найден: {path}"])
    except IsADirectoryError:
        raise ConfigError([f"это каталог, а не файл: {path}"])
    except json.JSONDecodeError as e:
        raise ConfigError([
            f"некорректный JSON: {e.msg} (строка {e.lineno}, "
            f"столбец {e.colno})"])
    except (OSError, UnicodeDecodeError) as e:
        raise ConfigError([f"не удалось прочитать '{path}': {e}"])
    if not isinstance(data, dict):
        raise ConfigError(["корень JSON должен быть объектом {...}"])
    return data


def _check_unknown(data, errors):
    """Отмечает параметры, которых нет в списке допустимых."""
    known = set(REQUIRED) | set(DEFAULTS)
    for key in sorted(set(data) - known):
        errors.append(f"{key}: неизвестный параметр")


def _check_bool(data, key, errors):
    """Значение логического параметра; None, если оно не bool."""
    value = data.get(key, DEFAULTS[key])
    if not isinstance(value, bool):
        errors.append(f"{key}: ожидается true или false")
        return None
    return value


def _check_package(data, test_mode, errors):
    """Проверяет имя пакета: большие буквы или groupId:artifactId."""
    value = data.get("package")
    if value is None:
        errors.append("package: параметр обязателен")
    elif not isinstance(value, str) or not value.strip():
        errors.append("package: ожидается непустая строка")
    elif test_mode and not TEST_NAME.match(value):
        errors.append(f"package: '{value}' - в тестовом режиме имя "
                      "состоит из больших латинских букв (например, A)")
    elif not test_mode and not MAVEN_NAME.match(value):
        errors.append(f"package: '{value}' - ожидается вид "
                      "groupId:artifactId")


def _check_file(path, errors):
    """Проверяет, что путь указывает на существующий файл."""
    if not os.path.exists(path):
        errors.append(f"repository: файл не найден: {path}")
    elif not os.path.isfile(path):
        errors.append(f"repository: это не файл: {path}")


def _check_repository(data, test_mode, errors):
    """Проверяет URL репозитория или путь к файлу тестового репозитория."""
    value = data.get("repository")
    if value is None:
        errors.append("repository: параметр обязателен")
    elif not isinstance(value, str) or not value.strip():
        errors.append("repository: ожидается непустая строка")
    elif test_mode:
        _check_file(value, errors)
    elif not value.startswith(URL_SCHEMES):
        errors.append("repository: URL должен начинаться с http://, "
                      "https:// или file://")


def _check_version(data, test_mode, errors):
    """Проверяет версию пакета (обязательна для Maven-репозитория)."""
    value = data.get("version")
    if value is None:
        if not test_mode:
            errors.append("version: параметр обязателен для Maven")
    elif not isinstance(value, str) or not VERSION.match(value):
        errors.append("version: ожидается строка вида 1.0.0")


def _check_depth(data, errors):
    """Проверяет максимальную глубину анализа."""
    value = data.get("max_depth", DEFAULTS["max_depth"])
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append("max_depth: ожидается целое число")
    elif value < MIN_DEPTH:
        errors.append("max_depth: число не должно быть отрицательным")


def _check_all(data):
    """Проверяет все параметры; возвращает список ошибок."""
    errors = []
    _check_unknown(data, errors)
    test_mode = _check_bool(data, "test_mode", errors)
    _check_bool(data, "ascii_tree", errors)
    reverse = _check_bool(data, "reverse", errors)
    if test_mode is None:
        return errors
    _check_package(data, test_mode, errors)
    _check_repository(data, test_mode, errors)
    _check_version(data, test_mode, errors)
    _check_depth(data, errors)
    if reverse and not test_mode:
        errors.append("reverse: обратные зависимости доступны только "
                      "для тестового репозитория (test_mode)")
    return errors


def load_config(path):
    """Читает и проверяет конфигурацию; возвращает Config."""
    data = _read_json(path)
    errors = _check_all(data)
    if errors:
        raise ConfigError(errors)
    return Config(**{**DEFAULTS, **data})
