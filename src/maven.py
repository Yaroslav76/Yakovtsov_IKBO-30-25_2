"""Чтение зависимостей из POM-файлов Maven-репозитория.

Используются только стандартные средства Python: urllib для загрузки
и xml.etree для разбора XML. Менеджеры пакетов не применяются.
"""
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as etree
from dataclasses import dataclass, field

TIMEOUT = 10
MAX_PARENTS = 10
MAX_SUBST = 10
SCOPES = ("compile", "runtime")
PLACEHOLDER = re.compile(r"\$\{([^}]+)\}")


class RepositoryError(Exception):
    """Ошибка загрузки или разбора данных репозитория."""


@dataclass(frozen=True)
class RawDep:
    """Зависимость из POM до подстановки свойств."""

    group: str
    artifact: str
    version: str
    scope: str
    optional: bool


@dataclass
class Pom:
    """Нужные нам сведения из POM-файла."""

    group: str
    artifact: str
    version: str
    parent: tuple = None
    properties: dict = field(default_factory=dict)
    managed: dict = field(default_factory=dict)
    deps: list = field(default_factory=list)


def _child_text(element, name):
    """Текст дочернего элемента name или None."""
    child = element.find(name)
    if child is None or child.text is None:
        return None
    return child.text.strip()


def _strip_namespaces(root):
    """Убирает пространства имён из имён тегов."""
    for element in root.iter():
        if isinstance(element.tag, str):
            element.tag = element.tag.rsplit("}", 1)[-1]


def _parse_parent(root):
    """Возвращает (groupId, artifactId, version) родителя или None."""
    parent = root.find("parent")
    if parent is None:
        return None
    return tuple(_child_text(parent, name)
                 for name in ("groupId", "artifactId", "version"))


def _parse_properties(root):
    """Словарь свойств из <properties>."""
    block = root.find("properties")
    if block is None:
        return {}
    return {child.tag: (child.text or "").strip() for child in block}


def _parse_dependency(element):
    """Разбирает элемент <dependency> в RawDep."""
    optional = _child_text(element, "optional") == "true"
    return RawDep(_child_text(element, "groupId"),
                  _child_text(element, "artifactId"),
                  _child_text(element, "version"),
                  _child_text(element, "scope"), optional)


def _parse_deps(block):
    """Список RawDep из элемента <dependencies> (или пустой)."""
    if block is None:
        return []
    return [_parse_dependency(item) for item in block.findall("dependency")]


def _parse_managed(root):
    """Словарь {(group, artifact): version} из dependencyManagement."""
    block = root.find("dependencyManagement/dependencies")
    return {(d.group, d.artifact): d.version
            for d in _parse_deps(block) if d.version}


def parse_pom(text):
    """Разбирает текст POM-файла в объект Pom."""
    try:
        root = etree.fromstring(text)
    except etree.ParseError as e:
        raise RepositoryError(f"некорректный XML в POM: {e}")
    _strip_namespaces(root)
    if root.tag != "project":
        raise RepositoryError("корневой элемент POM должен быть <project>")
    parent = _parse_parent(root)
    group = _child_text(root, "groupId") or (parent and parent[0])
    version = _child_text(root, "version") or (parent and parent[2])
    return Pom(group, _child_text(root, "artifactId"), version, parent,
               _parse_properties(root), _parse_managed(root),
               _parse_deps(root.find("dependencies")))


def _is_skipped(dep):
    """Зависимость не нужна: тестовая/provided/system или optional."""
    return (dep.scope or "compile") not in SCOPES or dep.optional


def _bad_version(version):
    """Версия пуста, не подставлена или задана диапазоном."""
    return version[:1] in ("", "[", "(") or "${" in version


def resolve(value, props):
    """Подставляет ${свойства} в строку value."""
    for _ in range(MAX_SUBST):
        new = PLACEHOLDER.sub(
            lambda m: props.get(m.group(1), m.group(0)), value)
        if new == value:
            break
        value = new
    return value


class MavenClient:
    """Загружает POM-файлы из репозитория и находит зависимости."""

    def __init__(self, repository, warnings, root):
        """repository - URL, warnings - список для предупреждений,
        root - узел 'group:artifact:version', ошибки которого фатальны."""
        self.repository = repository.rstrip("/")
        self.warnings = warnings
        self.root = root
        self.cache = {}

    def pom_url(self, group, artifact, version):
        """URL POM-файла по правилам раскладки Maven-репозитория."""
        folder = "/".join([group.replace(".", "/"), artifact, version])
        return f"{self.repository}/{folder}/{artifact}-{version}.pom"

    def fetch(self, url):
        """Скачивает текст по URL; ошибки сети - RepositoryError."""
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            raise RepositoryError(f"POM недоступен (HTTP {e.code}): {url}")
        except urllib.error.URLError as e:
            raise RepositoryError(f"репозиторий недоступен "
                                  f"({e.reason}): {url}")
        except (OSError, UnicodeDecodeError) as e:
            raise RepositoryError(f"не удалось прочитать {url}: {e}")

    def load_pom(self, group, artifact, version):
        """Возвращает Pom (с кэшированием)."""
        key = (group, artifact, version)
        if key not in self.cache:
            url = self.pom_url(group, artifact, version)
            self.cache[key] = parse_pom(self.fetch(url))
        return self.cache[key]

    def chain(self, pom):
        """Цепочка [pom, родитель, родитель родителя, ...]."""
        chain = [pom]
        while chain[-1].parent and len(chain) <= MAX_PARENTS:
            group, artifact, version = chain[-1].parent
            try:
                chain.append(self.load_pom(group, artifact, version))
            except RepositoryError as e:
                self.warnings.append(f"родительский POM: {e}")
                break
        return chain

    def properties(self, chain):
        """Свойства цепочки; дочерние переопределяют родительские."""
        props = {}
        for item in reversed(chain):
            props.update(item.properties)
        pom = chain[0]
        known = {"project.groupId": pom.group,
                 "project.artifactId": pom.artifact,
                 "project.version": pom.version,
                 "pom.version": pom.version, "version": pom.version,
                 "project.parent.version": pom.parent and pom.parent[2]}
        props.update({k: v for k, v in known.items() if v})
        return props

    def managed(self, chain, props):
        """Версии из dependencyManagement всей цепочки."""
        result = {}
        for item in reversed(chain):
            for (group, artifact), version in item.managed.items():
                key = (resolve(group, props), resolve(artifact, props))
                result[key] = resolve(version, props)
        return result

    def dependencies(self, node):
        """Прямые зависимости узла 'group:artifact:version'."""
        try:
            pom = self.load_pom(*node.split(":"))
        except RepositoryError as e:
            if node == self.root:
                raise
            self.warnings.append(f"{node}: {e}")
            return []
        chain = self.chain(pom)
        props = self.properties(chain)
        managed = self.managed(chain, props)
        found = (self.dep_node(d, props, managed) for d in pom.deps)
        return list(dict.fromkeys(n for n in found if n))

    def dep_node(self, dep, props, managed):
        """Узел 'g:a:v' для зависимости или None, если она не нужна."""
        if _is_skipped(dep):
            return None
        group = resolve(dep.group or "", props)
        artifact = resolve(dep.artifact or "", props)
        version = resolve(dep.version or "", props)
        version = version or managed.get((group, artifact), "")
        if not (group and artifact) or _bad_version(version):
            self.warnings.append(
                f"{group}:{artifact}: версия не определена, пропущена")
            return None
        return f"{group}:{artifact}:{version}"
