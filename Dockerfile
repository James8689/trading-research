# Operator dashboard
#
# Single-user control plane for the research network. Stdlib only.
# Bind 0.0.0.0 and put a password in DASHBOARD_PASSWORD. Mount research_state
# as a volume so SQLite (network, improvement, budget, families, UI) survives
# process and host restarts.

FROM python:3.12-slim
WORKDIR /app
COPY . .
EXPOSE 8787
ENV DASHBOARD_HOST=0.0.0.0
ENV DASHBOARD_PORT=8787
VOLUME ["/app/research_state"]
CMD ["python", "go.py", "--mode", "dashboard"]
