FROM python:3.14-slim

WORKDIR /app

# System deps for Selenium
RUN apt-get update && apt-get install -y \
    wget curl firefox-esr \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App
COPY . .

# Web UI port
EXPOSE 8233

ENTRYPOINT ["python", "-m", "briar.cli"]
