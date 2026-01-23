# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
# build-essential and libpq-dev are often needed for python packages (like psycopg2)
# gettext is useful for Django translations
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy project configuration files
COPY pyproject.toml poetry.lock ./

# Configure Poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
# --no-root: Do not install the current project as a package
RUN poetry install --no-root --no-interaction --no-ansi

# Copy the project code
COPY . .

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Expose port (adjust if your app runs on a different port)
EXPOSE 8000

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
