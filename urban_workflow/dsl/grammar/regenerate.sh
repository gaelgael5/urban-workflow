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

# Maven Central répond parfois 429 (limitation de débit) : on bascule sur le
# miroir Google, qui sert les mêmes artefacts. `--fail` est indispensable —
# sans lui, curl écrit la page d'erreur dans le jar et java échoue plus loin
# sur un fichier illisible.
CHEMIN="org/antlr/antlr4/${ANTLR_VERSION}/antlr4-${ANTLR_VERSION}-complete.jar"
MIROIRS=(
    "https://repo1.maven.org/maven2/${CHEMIN}"
    "https://maven-central.storage-download.googleapis.com/maven2/${CHEMIN}"
)

if [ ! -f "$JAR" ]; then
    for url in "${MIROIRS[@]}"; do
        echo "Téléchargement d'ANTLR ${ANTLR_VERSION} depuis ${url}…"
        if curl -sSL --fail -o "$JAR" "$url"; then
            break
        fi
        echo "  échec, miroir suivant…" >&2
        rm -f "$JAR"
    done
    if [ ! -f "$JAR" ]; then
        echo "Impossible de récupérer le jar ANTLR ${ANTLR_VERSION}." >&2
        echo "Le télécharger à la main, puis : ANTLR_JAR=/chemin/vers.jar $0" >&2
        exit 1
    fi
fi

java -jar "$JAR" -Dlanguage=Python3 -o ../generated WorkflowLexer.g4
java -jar "$JAR" -Dlanguage=Python3 -visitor -no-listener \
    -lib ../generated -o ../generated WorkflowParser.g4

echo "OK — parseur régénéré dans urban_workflow/dsl/generated/"
