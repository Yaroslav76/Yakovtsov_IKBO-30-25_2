"""Построение графа зависимостей обходом в ширину (BFS) без рекурсии."""
from collections import deque


def build_graph(root, max_depth, get_deps):
    """Строит граф от корня обходом в ширину.

    get_deps(узел) возвращает список зависимостей узла. Узлы на глубине
    max_depth попадают в граф, но не раскрываются. Повторно посещённые
    узлы не обходятся заново, поэтому циклы не приводят к зацикливанию.
    Возвращает {узел: [зависимости]} в порядке обхода.
    """
    graph = {}
    seen = {root}
    queue = deque([(root, 0)])
    while queue:
        node, depth = queue.popleft()
        children = get_deps(node) if depth < max_depth else []
        graph[node] = list(children)
        for child in children:
            if child not in seen:
                seen.add(child)
                queue.append((child, depth + 1))
    return graph


def has_cycle(graph):
    """Есть ли в графе цикл (алгоритм Кана, без рекурсии)."""
    incoming = dict.fromkeys(graph, 0)
    for children in graph.values():
        for child in children:
            incoming[child] = incoming.get(child, 0) + 1
    queue = deque(node for node, count in incoming.items() if not count)
    removed = 0
    while queue:
        node = queue.popleft()
        removed += 1
        for child in graph.get(node, []):
            incoming[child] -= 1
            if not incoming[child]:
                queue.append(child)
    return removed != len(incoming)


def invert(graph):
    """Обращает рёбра: {узел: [кто от него зависит]}."""
    result = {node: [] for node in graph}
    for node, children in graph.items():
        for child in children:
            result.setdefault(child, []).append(node)
    return result


def edges(graph, reverse=False):
    """Список рёбер (зависимый, зависимость).

    Для графа обратных зависимостей (reverse=True) рёбра разворачиваются
    обратно, чтобы стрелка всегда шла от зависимого пакета к зависимости.
    """
    pairs = [(node, child) for node, children in graph.items()
             for child in children]
    return [(b, a) for a, b in pairs] if reverse else pairs
