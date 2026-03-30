# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy minimal requirements file for MCP server
COPY requirements-mcp.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and data
COPY budget-reports-mcp-server.py .
COPY data/ ./data/

# Expose port 8000 (Azure Container Apps default)
EXPOSE 8000

# Run the FastMCP server with streamable-http transport
# Using port 8000 and binding to 0.0.0.0 for container access
CMD ["fastmcp", "run", "budget-reports-mcp-server.py", "--transport", "streamable-http", "--port", "8000", "--host", "0.0.0.0"]

