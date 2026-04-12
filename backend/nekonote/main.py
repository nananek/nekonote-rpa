from __future__ import annotations

import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Nekonote RPA Backend")
    parser.add_argument("--stdio", action="store_true", help="Run in stdio mode (no TCP)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18080)
    args = parser.parse_args()

    if args.stdio:
        from nekonote.stdio_server import run_stdio
        run_stdio()
    else:
        import uvicorn
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from nekonote.api.routes import router
        from nekonote.api.websocket import websocket_endpoint

        app = FastAPI(title="Nekonote RPA Engine", version="0.1.0")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
        app.include_router(router)
        app.websocket("/ws/execution")(websocket_endpoint)
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
