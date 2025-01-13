# Use an official Python image
FROM python:3.12-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install Poetry via pip
RUN pip install --no-cache-dir poetry

# Copy only the necessary files for dependency installation
COPY pyproject.toml poetry.lock /app/

# Export Poetry dependencies to requirements.txt
RUN poetry export --without-hashes -f requirements.txt -o proj_requirements.txt

# Install dependencies using pip
RUN pip install --no-cache-dir -r proj_requirements.txt

# Copy the project files
COPY . /app/

# Expose the port Django runs on
EXPOSE 8000

# Add an entrypoint script to handle initial commands
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Default entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]