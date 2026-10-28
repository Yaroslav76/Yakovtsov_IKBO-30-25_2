"""Модульные тесты разбора файла тестового репозитория."""
import os
import unittest

import helpers
import testrepo


class TestRepoTests(unittest.TestCase):
    """Разбор формата 'A: B C'."""

    def test_parse(self):
        """Обычный граф, комментарии и пустые строки."""
        graph = testrepo.parse_graph("# комментарий\n\nA: B C\nB: C\n")
        self.assertEqual(graph, {"A": ["B", "C"], "B": ["C"], "C": []})

    def test_duplicates_in_deps(self):
        """Повтор зависимости в строке убирается."""
        graph = testrepo.parse_graph("A: B B\n")
        self.assertEqual(graph["A"], ["B"])

    def test_errors(self):
        """Неверные строки, имена и повторное описание пакета."""
        for text in ("A B C\n", "a: B\n", "A: b\n", "A:\nA: B\n"):
            with self.assertRaises(testrepo.TestRepoError):
                testrepo.parse_graph(text)

    def test_load_file(self):
        """Чтение настоящего файла и отсутствующего файла."""
        path = os.path.join(helpers.DATA, "graph_basic.txt")
        self.assertIn("A", testrepo.load_graph(path))
        with self.assertRaises(testrepo.TestRepoError):
            testrepo.load_graph("no_such_file.txt")


if __name__ == "__main__":
    unittest.main()
