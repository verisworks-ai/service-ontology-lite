"""HTTP server wrapper for FastMCP service-ontology-lite."""

from .mcp_server import create_app


def main():
    """Run FastMCP HTTP server on 0.0.0.0:8000."""
    import uvicorn

    # Create FastMCP app
    mcp = create_app()

    # Get Starlette/FastAPI app
    http_app = mcp.http_app()

    # Run with uvicorn
    uvicorn.run(http_app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
