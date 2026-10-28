"""Текстовое представление графа: ASCII-дерево и язык диаграмм D2."""
from src import graph as graph_ops

BRANCH = "├── "
LAST = "└── "
PIPE = "│   "
SPACE = "    "
MARK_CYCLE = " (цикл)"
MARK_REPEAT = " (повтор)"


def _mark(node, path, expanded, graph):
    """Пометка узла: цикл (предок), повтор (уже раскрыт) или пусто."""
    if node in path:
        return MARK_CYCLE
    if node in expanded and graph.get(node):
        return MARK_REPEAT
    return ""


def _children(node, graph, prefix, path):
    """Элементы стека для потомков узла (в обратном порядке)."""
    children = graph.get(node, [])
    last_index = len(children) - 1
    items = [(child, prefix, index == last_index, path)
             for index, child in enumerate(children)]
    return items[::-1]


def ascii_tree(root, graph):
    """ASCII-дерево зависимостей от корня (обход со стеком, без рекурсии).

    Узел, уже раскрытый выше, помечается (повтор) и не раскрывается;
    возврат к предку помечается (цикл).
    """
    lines = [root]
    expanded = {root}
    stack = _children(root, graph, "", (root,))
    while stack:
        node, prefix, last, path = stack.pop()
        mark = _mark(node, path, expanded, graph)
        lines.append(prefix + (LAST if last else BRANCH) + node + mark)
        if mark:
            continue
        expanded.add(node)
        indent = prefix + (SPACE if last else PIPE)
        stack.extend(_children(node, graph, indent, path + (node,)))
    return "\n".join(lines)


def quote(name):
    """Имя узла в кавычках по правилам D2."""
    escaped = name.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def d2(graph, reverse=False):
    """Описание графа на языке диаграмм D2: рёбра 'A -> B'."""
    pairs = graph_ops.edges(graph, reverse)
    used = {node for pair in pairs for node in pair}
    lines = [quote(node) for node in graph if node not in used]
    lines += [f"{quote(a)} -> {quote(b)}" for a, b in pairs]
    return "\n".join(lines)
