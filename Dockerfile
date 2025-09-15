# Start with a small, modern Python runtime. Use an explicit slim image.
FROM python:3.12-slim


# Set a working directory in the container
WORKDIR /app


# Copy only requirements first to leverage Docker caching
COPY requirements.txt ./


# Install packages; --no-cache-dir keeps image small
RUN python -m pip install --upgrade pip \
&& python -m pip install --no-cache-dir -r requirements.txt


# Copy the rest of the project
COPY . .


# Use a non-root user if you care about security (optional). For simplicity start as default.
ENV PYTHONUNBUFFERED=1


# Default command — configurable via docker-compose or override at runtime
CMD ["python", "main.py", "--config", "config.json"]
