"""Обработчики этапов: что именно выводит приложение на каждом этапе."""
import sys

import graph as graph_ops
import maven
import render
import testrepo

DATA_ERRORS = (maven.RepositoryError, testrepo.TestRepoError)


def _fmt(value):
    """Значение параметра в виде текста (true/false для логических)."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def stage1(cfg):
    """Этап 1: вывод всех параметров в формате ключ-значение."""
    for key, value in cfg.pairs():
        print(f"{key}: {_fmt(value)}")
    return 0


def root_node(cfg):
    """Имя корневого узла: пакет (тест) или group:artifact:version."""
    return cfg.package if cfg.test_mode else f"{cfg.package}:{cfg.version}"


def make_provider(cfg, warnings):
    """Функция узел -> список зависимостей для выбранного репозитория."""
    if cfg.test_mode:
        graph = testrepo.load_graph(cfg.repository)
        if cfg.package not in graph:
            raise testrepo.TestRepoError(
                f"пакет '{cfg.package}' не найден в тестовом репозитории")
        if cfg.reverse:
            graph = graph_ops.invert(graph)
        return lambda node: graph.get(node, [])
    client = maven.MavenClient(cfg.repository, warnings, root_node(cfg))
    return client.dependencies


def report(warnings):
    """Печатает предупреждения в поток ошибок."""
    for message in warnings:
        print(f"Предупреждение: {message}", file=sys.stderr)


def stage2(cfg):
    """Этап 2: прямые зависимости заданного пакета."""
    warnings = []
    root = root_node(cfg)
    deps = make_provider(cfg, warnings)(root)
    print(f"Прямые зависимости {root}:")
    for dep in deps:
        print(f"  {dep}")
    if not deps:
        print("  (нет)")
    report(warnings)
    return 0


def compute_graph(cfg, warnings):
    """Граф зависимостей от корня с учётом максимальной глубины."""
    provider = make_provider(cfg, warnings)
    return graph_ops.build_graph(root_node(cfg), cfg.max_depth, provider)


def print_graph(title, graph):
    """Печатает граф списком 'узел -> зависимости' и признак циклов."""
    print(title)
    for node, deps in graph.items():
        print(f"  {node} -> {', '.join(deps) if deps else '(нет)'}")
    cycles = "да" if graph_ops.has_cycle(graph) else "нет"
    print(f"Циклические зависимости: {cycles}")


def stage3(cfg):
    """Этап 3: граф зависимостей (BFS, глубина, циклы)."""
    warnings = []
    graph = compute_graph(cfg, warnings)
    print_graph(f"Граф зависимостей {root_node(cfg)} "
                f"(глубина не больше {cfg.max_depth}):", graph)
    report(warnings)
    return 0


def stage4(cfg):
    """Этап 4: обратные зависимости (кто зависит от пакета) тем же BFS."""
    if not cfg.reverse:
        return stage3(cfg)
    warnings = []
    graph = compute_graph(cfg, warnings)
    print(f"Обратные зависимости {root_node(cfg)} - пакеты, которые от него "
          f"зависят (глубина не больше {cfg.max_depth}).")
    print_graph("Запись 'X -> Y' читается так: от X зависит Y:", graph)
    report(warnings)
    return 0


def stage5(cfg):
    """Этап 5: описание графа на языке D2 и (по параметру) ASCII-дерево."""
    warnings = []
    graph = compute_graph(cfg, warnings)
    print("Описание графа на языке D2:")
    print(render.d2(graph, cfg.reverse))
    if cfg.ascii_tree:
        print("ASCII-дерево зависимостей:")
        print(render.ascii_tree(root_node(cfg), graph))
    report(warnings)
    return 0


HANDLERS = {1: stage1, 2: stage2, 3: stage3, 4: stage4, 5: stage5}
