FROM python:3.11-slim

WORKDIR /app

# Install git (needed for MCP)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./mcp_server /app/mcp_server

EXPOSE 7000

ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=7000
ENV DEBUG=true
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1