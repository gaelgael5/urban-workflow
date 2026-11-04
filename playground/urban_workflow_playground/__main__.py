"""``python -m urban_workflow_playground`` — démarre le serveur du playground."""

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
