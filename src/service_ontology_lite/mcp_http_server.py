"""HTTP server wrapper for FastMCP service-ontology-lite."""

import argparse
import os

from .mcp_server import create_app


def main():
    """Run FastMCP HTTP server. Defaults to 127.0.0.1 to prevent accidental LAN exposure."""
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"),
                        help="Bind address (default: 127.0.0.1). Use 0.0.0.0 only behind a reverse proxy.")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    args = parser.parse_args()

    mcp = create_app()
    http_app = mcp.http_app()
    uvicorn.run(http_app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
