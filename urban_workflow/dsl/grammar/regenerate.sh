#!/usr/bin/env bash
# Régénère le parseur Python du DSL depuis les grammaires ANTLR.
#
# Les grammaires (WorkflowLexer.g4, WorkflowParser.g4) sont reprises telles
# quelles du projet source Black-Beard-Sdk/Workflow ; le code généré est
# commité dans ../generated/ et ne doit jamais être édité à la main.
#
# Prérequis :
#   - java >= 11 ;
#   - le jar ANTLR 4.13.2 — la MÊME version que le runtime
#     antlr4-python3-runtime apporté par urban-json. Toute montée de version
#     doit se faire conjointement (jar + runtime).
#
# Le jar est téléchargé depuis Maven Central si absent (www.antlr.org peut
# être inaccessible depuis certains environnements).

set -euo pipefail
cd "$(dirname "$0")"

ANTLR_VERSION=4.13.2
JAR="${ANTLR_JAR:-/tmp/antlr-${ANTLR_VERSION}-complete.jar}"

if [ ! -f "$JAR" ]; then
    echo "Téléchargement d'ANTLR ${ANTLR_VERSION} vers ${JAR}…"
    curl -sSL -o "$JAR" \
        "https://repo1.maven.org/maven2/org/antlr/antlr4/${ANTLR_VERSION}/antlr4-${ANTLR_VERSION}-complete.jar"
fi

java -jar "$JAR" -Dlanguage=Python3 -o ../generated WorkflowLexer.g4
java -jar "$JAR" -Dlanguage=Python3 -visitor -no-listener \
    -lib ../generated -o ../generated WorkflowParser.g4

echo "OK — parseur régénéré dans urban_workflow/dsl/generated/"
