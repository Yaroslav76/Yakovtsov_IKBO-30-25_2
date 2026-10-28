"""Модульные тесты ASCII-дерева и описания D2."""
import unittest

import graph
import render

DEMO = {"A": ["B", "C"], "B": ["D", "E"], "C": ["E", "F"], "D": ["G"],
        "E": ["G"], "F": ["A"], "G": []}


class AsciiTreeTests(unittest.TestCase):
    """Вывод дерева."""

    def test_simple(self):
        """Простое дерево с ветвями и последним потомком."""
        tree = render.ascii_tree("A", {"A": ["B", "C"], "B": [], "C": []})
        self.assertEqual(tree, "A\n├── B\n└── C")

    def test_nesting_prefix(self):
        """Вертикальная линия у непоследних веток."""
        tree = render.ascii_tree("A", {"A": ["B", "C"], "B": ["D"],
                                       "C": [], "D": []})
        self.assertEqual(tree, "A\n├── B\n│   └── D\n└── C")

    def test_cycle_and_repeat(self):
        """Возврат к предку - (цикл), повторное раскрытие - (повтор)."""
        tree = render.ascii_tree("A", DEMO)
        self.assertIn("A (цикл)", tree)
        self.assertIn("E (повтор)", tree)

    def test_only_root(self):
        """Корень без зависимостей."""
        self.assertEqual(render.ascii_tree("A", {"A": []}), "A")


class D2Tests(unittest.TestCase):
    """Вывод на языке D2."""

    def test_edges(self):
        """Рёбра в кавычках, одиночный узел объявляется отдельно."""
        self.assertEqual(render.d2({"A": ["B"], "B": []}), '"A" -> "B"')
        self.assertEqual(render.d2({"A": []}), '"A"')

    def test_maven_names_and_reverse(self):
        """Имена с двоеточием; обратный режим разворачивает стрелки."""
        self.assertEqual(render.quote("org.x:lib:1"), '"org.x:lib:1"')
        rev = graph.invert({"A": ["B"], "B": []})
        self.assertEqual(render.d2(rev, reverse=True), '"A" -> "B"')

    def test_escape(self):
        """Кавычки и обратная косая черта экранируются."""
        self.assertEqual(render.quote('a"b'), '"a\\"b"')


if __name__ == "__main__":
    unittest.main()
