#!/usr/bin/env bash
# Дерево зависимостей штатным инструментом: bash tests/compare_mvn.sh g:a:v
# Нужны установленные Maven (mvn) и доступ в интернет.
IFS=: read -r GROUP ARTIFACT VERSION <<< "$1"
[ -z "$VERSION" ] && { echo "usage: $0 groupId:artifactId:version"; exit 2; }
DIR=$(mktemp -d)
cat > "$DIR/pom.xml" <<POM
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>local</groupId><artifactId>probe</artifactId>
  <version>1</version>
  <dependencies>
    <dependency>
      <groupId>$GROUP</groupId><artifactId>$ARTIFACT</artifactId>
      <version>$VERSION</version>
    </dependency>
  </dependencies>
</project>
POM
(cd "$DIR" && mvn -q dependency:tree)
rm -rf "$DIR"
