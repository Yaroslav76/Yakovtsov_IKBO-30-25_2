"""Модульные тесты чтения POM и зависимостей из репозитория."""
import functools
import http.server
import threading
import unittest

import helpers
import maven

POM = """<project xmlns="http://maven.apache.org/POM/4.0.0">
  <artifactId>x</artifactId><version>1</version>
  <parent><groupId>g</groupId><artifactId>p</artifactId>
  <version>7</version></parent>
  <properties><v>2.0</v></properties>
  <dependencies>
    <dependency><groupId>g</groupId><artifactId>a</artifactId>
    <version>${v}</version></dependency>
    <dependency><groupId>g</groupId><artifactId>t</artifactId>
    <version>1</version><scope>test</scope></dependency>
  </dependencies>
</project>"""


class ParsePomTests(unittest.TestCase):
    """Разбор текста POM без сети."""

    def test_namespace_and_parent(self):
        """Пространство имён убирается, группа берётся у родителя."""
        pom = maven.parse_pom(POM)
        self.assertEqual(pom.group, "g")
        self.assertEqual(pom.artifact, "x")
        self.assertEqual(len(pom.deps), 2)

    def test_resolve_properties(self):
        """Подстановка ${свойства}, включая неизвестные."""
        props = {"v": "2.0"}
        self.assertEqual(maven.resolve("a-${v}", props), "a-2.0")
        self.assertEqual(maven.resolve("${no}", props), "${no}")

    def test_bad_xml(self):
        """Некорректный XML и неверный корневой элемент."""
        with self.assertRaises(maven.RepositoryError):
            maven.parse_pom("<project><oops></project>")
        with self.assertRaises(maven.RepositoryError):
            maven.parse_pom("<other/>")


class ClientTests(unittest.TestCase):
    """Работа клиента с тестовым HTTP-репозиторием."""

    @classmethod
    def setUpClass(cls):
        """Запускает локальный HTTP-сервер с каталогом mock_repo."""
        handler = functools.partial(
            http.server.SimpleHTTPRequestHandler,
            directory=helpers.MOCK_REPO)
        handler.log_message = lambda *args: None
        cls.server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), handler)
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"
        threading.Thread(target=cls.server.serve_forever,
                         daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        """Останавливает сервер."""
        cls.server.shutdown()
        cls.server.server_close()

    def client(self, root):
        """Новый клиент и список его предупреждений."""
        warnings = []
        return maven.MavenClient(self.url, warnings, root), warnings

    def test_direct_dependencies(self):
        """Наследование свойств и версий, пропуск test/provided/optional."""
        root = "org.example:app:1.0"
        client, warnings = self.client(root)
        self.assertEqual(client.dependencies(root), [
            "org.example:lib-a:2.0", "org.example:lib-b:1.5",
            "org.example:ghost:1.0"])
        self.assertEqual(len(warnings), 1)

    def test_leaf(self):
        """Пакет без зависимостей."""
        root = "org.example:lib-c:1.0"
        client, _ = self.client(root)
        self.assertEqual(client.dependencies(root), [])

    def test_missing_root_is_error(self):
        """Отсутствующий корневой POM - ошибка."""
        root = "org.example:ghost:1.0"
        client, _ = self.client(root)
        with self.assertRaises(maven.RepositoryError):
            client.dependencies(root)

    def test_missing_child_is_warning(self):
        """Отсутствующий POM не корня - предупреждение и пустой список."""
        client, warnings = self.client("org.example:app:1.0")
        self.assertEqual(client.dependencies("org.example:ghost:1.0"), [])
        self.assertEqual(len(warnings), 1)


if __name__ == "__main__":
    unittest.main()
