FROM python:3.12-slim

WORKDIR /app

# Create a non-root user: required for EKS security policies
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Hand ownership to the non-root user
RUN chown -R appuser:appgroup /app
USER appuser

# EKS ingress routes to 8080: avoids needing CAP_NET_BIND_SERVICE for port <1024
EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
