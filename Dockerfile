FROM python:3.11-slim

WORKDIR /app

# Install basic utilities
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser AND all required Linux system shared libraries
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application source code
COPY . .

CMD ["python", "croma_tracker.py"]
