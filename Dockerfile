FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code (.env is excluded via .dockerignore)
COPY . .

# -u = unbuffered output so logs show up immediately in `docker compose logs`
CMD ["python", "-u", "main.py"]
