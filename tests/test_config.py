"""Модульные тесты проверки конфигурации."""
import os
import unittest

import helpers
from config import ConfigError, load_config

GRAPH = os.path.join(helpers.DATA, "graph_basic.txt")


def maven(**extra):
    """Корректная Maven-конфигурация с изменениями extra."""
    base = {"package": "org.example:app", "version": "1.0",
            "repository": "http://localhost:8765"}
    return {**base, **extra}


def test_cfg(**extra):
    """Корректная конфигурация тестового режима с изменениями extra."""
    base = {"package": "A", "repository": GRAPH, "test_mode": True}
    return {**base, **extra}


class ConfigTests(unittest.TestCase):
    """Проверка допустимых и недопустимых параметров."""

    def errors(self, data):
        """Возвращает список ошибок для конфигурации data."""
        path = helpers.write_json(data)
        self.addCleanup(os.remove, path)
        with self.assertRaises(ConfigError) as ctx:
            load_config(path)
        return ctx.exception.errors

    def test_valid_maven(self):
        """Корректная Maven-конфигурация загружается с умолчаниями."""
        path = helpers.write_json(maven())
        self.addCleanup(os.remove, path)
        cfg = load_config(path)
        self.assertEqual(cfg.package, "org.example:app")
        self.assertEqual(cfg.max_depth, 3)
        self.assertFalse(cfg.test_mode)

    def test_valid_test_mode(self):
        """Корректная конфигурация тестового режима."""
        path = helpers.write_json(test_cfg(max_depth=0))
        self.addCleanup(os.remove, path)
        self.assertEqual(load_config(path).max_depth, 0)

    def test_missing_file(self):
        """Отсутствующий файл конфигурации."""
        with self.assertRaises(ConfigError):
            load_config("no_such_config.json")

    def test_package_errors(self):
        """Неверное имя пакета в обоих режимах."""
        self.assertTrue(self.errors(maven(package="app")))
        self.assertTrue(self.errors(test_cfg(package="ab")))
        self.assertTrue(self.errors(maven(package="")))

    def test_version_required(self):
        """Версия обязательна для Maven и должна быть корректной."""
        data = maven()
        del data["version"]
        self.assertTrue(self.errors(data))
        self.assertTrue(self.errors(maven(version="1 0")))

    def test_repository_errors(self):
        """Неверный URL и несуществующий файл репозитория."""
        self.assertTrue(self.errors(maven(repository="ftp://x")))
        self.assertTrue(self.errors(test_cfg(repository="no_file.txt")))
        self.assertTrue(self.errors(test_cfg(repository=helpers.DATA)))

    def test_depth_errors(self):
        """Неверная глубина: отрицательная, строка, логическое."""
        self.assertTrue(self.errors(test_cfg(max_depth=-1)))
        self.assertTrue(self.errors(test_cfg(max_depth="3")))
        self.assertTrue(self.errors(test_cfg(max_depth=True)))

    def test_bool_errors(self):
        """Логические параметры принимают только true и false."""
        self.assertTrue(self.errors(test_cfg(ascii_tree=1)))
        self.assertTrue(self.errors(test_cfg(test_mode="yes")))

    def test_unknown_and_reverse(self):
        """Неизвестный параметр и reverse вне тестового режима."""
        self.assertTrue(self.errors(test_cfg(color="red")))
        self.assertTrue(self.errors(maven(reverse=True)))


if __name__ == "__main__":
    unittest.main()
