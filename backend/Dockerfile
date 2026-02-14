FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
# Install system dependencies
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Copy entrypoint script
COPY scripts/entrypoint.sh /app/scripts/
RUN sed -i 's/\r$//g' /app/scripts/entrypoint.sh
RUN chmod +x /app/scripts/entrypoint.sh

# Entrypoint
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
