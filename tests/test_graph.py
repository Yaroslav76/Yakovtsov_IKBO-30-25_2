"""Модульные тесты построения графа и поиска циклов."""
import unittest

import helpers
import graph

REPO = {"A": ["B", "C"], "B": ["D"], "C": ["D", "E"], "D": [], "E": []}
CYCLE = {"A": ["B"], "B": ["C"], "C": ["A", "D"], "D": []}
SELF = {"X": ["X", "Y"], "Y": ["X"]}
ROOT = helpers.ROOT


def getter(repo):
    """Функция получения зависимостей по словарю."""
    return lambda node: repo.get(node, [])


class BuildGraphTests(unittest.TestCase):
    """Обход в ширину с глубиной и циклами."""

    def test_full(self):
        """Полный обход; порядок узлов - по уровням."""
        result = graph.build_graph("A", 5, getter(REPO))
        self.assertEqual(list(result), ["A", "B", "C", "D", "E"])
        self.assertEqual(result["C"], ["D", "E"])

    def test_depth_limit(self):
        """Глубина 1: потомки корня есть, но не раскрываются."""
        result = graph.build_graph("A", 1, getter(REPO))
        self.assertEqual(result, {"A": ["B", "C"], "B": [], "C": []})

    def test_depth_zero(self):
        """Глубина 0: только корень без зависимостей."""
        self.assertEqual(graph.build_graph("A", 0, getter(REPO)),
                         {"A": []})

    def test_cycles_terminate(self):
        """Цикл и самозависимость не приводят к зацикливанию."""
        result = graph.build_graph("A", 99, getter(CYCLE))
        self.assertEqual(len(result), 4)
        loop = graph.build_graph("X", 99, getter(SELF))
        self.assertEqual(loop, SELF)

    def test_no_recursion_on_deep_chain(self):
        """Очень длинная цепочка обходится без переполнения стека."""
        size = 5000
        chain = {str(i): [str(i + 1)] for i in range(size)}
        result = graph.build_graph("0", size, getter(chain))
        self.assertEqual(len(result), size + 1)


class ReverseTests(unittest.TestCase):
    """Обратные зависимости тем же обходом."""

    def test_invert(self):
        """Рёбра меняют направление."""
        rev = graph.invert(REPO)
        self.assertEqual(rev["D"], ["B", "C"])
        self.assertEqual(rev["A"], [])

    def test_reverse_bfs(self):
        """Кто (транзитивно) зависит от E."""
        result = graph.build_graph("E", 5, getter(graph.invert(REPO)))
        self.assertEqual(list(result), ["E", "C", "A"])

    def test_reverse_depth(self):
        """Ограничение глубины в обратном режиме."""
        result = graph.build_graph("D", 1, getter(graph.invert(REPO)))
        self.assertEqual(result, {"D": ["B", "C"], "B": [], "C": []})


class CycleTests(unittest.TestCase):
    """Поиск циклов."""

    def test_has_cycle(self):
        """Граф с циклом, с самопетлёй и без циклов."""
        self.assertTrue(graph.has_cycle(CYCLE))
        self.assertTrue(graph.has_cycle(SELF))
        self.assertFalse(graph.has_cycle(REPO))


if __name__ == "__main__":
    unittest.main()
