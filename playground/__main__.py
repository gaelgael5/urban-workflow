"""``python -m playground`` — démarre le serveur du playground."""

import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "playground.app:app",
        host=os.environ.get("PLAYGROUND_HOST", "127.0.0.1"),
        port=int(os.environ.get("PLAYGROUND_PORT", "8777")),
        reload=False,
    )
