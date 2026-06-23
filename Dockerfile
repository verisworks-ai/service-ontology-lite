FROM python:3.11-slim

WORKDIR /app

# Install the package
COPY . .
RUN pip install --no-cache-dir -e .

# Expose HTTP port
EXPOSE 8000

# Run FastMCP HTTP server (listens on 0.0.0.0:8000)
CMD ["service-ontology-mcp-http"]
