# Image du playground urban-workflow (IHM de test). Contexte de build = racine
# du dépôt (cf. docker-compose.yml) : le moteur ET le playground sont installés
# DEPUIS LES SOURCES du dépôt, pas depuis PyPI, pour que la machine de test
# serve exactement ce que porte la branche déployée (le playground déclare
# `urban-workflow>=0.2.0` : sans l'install du socle local, pip irait le tirer
# de PyPI et on testerait une autre version du moteur).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /src
COPY pyproject.toml README.md README.en.md LICENSE ./
COPY urban_workflow urban_workflow
COPY playground playground

# Install non éditable : l'image ne dépend plus de /src à l'exécution. Extra
# [schemas] seul : le playground valide des schémas YAML ; [sql] n'est pas
# utilisé par l'IHM, donc non installé.
RUN pip install "./[schemas]" ./playground \
    && useradd --system --uid 10001 --no-create-home playground \
    && mkdir -p /data/layouts && chown playground /data/layouts

# Mise en page des diagrammes : fichiers <workflow>.layout.json servis par
# GET/PUT /api/layout/{workflow}. Le répertoire existe dans l'image avec le
# bon propriétaire : un volume nommé monté dessus en hérite à sa création
# (sinon il appartiendrait à root et l'utilisateur non root ne pourrait
# pas y écrire).
ENV PLAYGROUND_LAYOUT_DIR=/data/layouts

USER playground
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status == 200 else 1)"

# uvicorn appelé directement (et non `python -m urban_workflow_playground`) :
# le point d'entrée écoute 127.0.0.1 par défaut, injoignable depuis l'hôte.
CMD ["uvicorn", "urban_workflow_playground.app:app", "--host", "0.0.0.0", "--port", "8000"]
