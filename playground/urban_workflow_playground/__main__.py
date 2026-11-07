"""``python -m urban_workflow_playground`` — démarre le serveur du playground.

Variables d'environnement : ``PLAYGROUND_HOST``, ``PLAYGROUND_PORT`` et
``PLAYGROUND_LAYOUT_DIR`` (répertoire des fichiers ``<workflow>.layout.json``
de la mise en page des diagrammes ; sans elle, le navigateur garde les
positions dans son propre stockage).
"""

import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "urban_workflow_playground.app:app",
        host=os.environ.get("PLAYGROUND_HOST", "127.0.0.1"),
        port=int(os.environ.get("PLAYGROUND_PORT", "8777")),
        reload=False,
    )


if __name__ == "__main__":
    main()
