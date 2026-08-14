FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim

# Non-root: the app doesn't need root, and it lets us bind an unprivileged port.
# --home is required: `adduser --system` otherwise defaults to HOME=/nonexistent,
# and Python's --user site-packages lookup (below) resolves against $HOME.
RUN addgroup --system appgroup && adduser --system --home /home/appuser --ingroup appgroup appuser

WORKDIR /app

COPY --from=builder /root/.local /home/appuser/.local
COPY . .
RUN chown -R appuser:appgroup /app

USER appuser
ENV HOME=/home/appuser
ENV PATH=/home/appuser/.local/bin:$PATH

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
