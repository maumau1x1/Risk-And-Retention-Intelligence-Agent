FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir -e ".[apps]"

ENV MCP_SERVER_HOST=0.0.0.0
ENV MCP_SERVER_PORT=8080
ENV PYTHONPATH=/app/src

EXPOSE 8080

CMD ["python", "-m", "risk_agent_mcp.main"]
