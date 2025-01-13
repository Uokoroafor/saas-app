ARG PYTHON_VERSION=3.12-slim-bullseye
FROM python:${PYTHON_VERSION}

# Create a venv
RUN python -m venv /opt/.venv

# Set the Virtual Environment as current location
ENV PATH=/opt/.venv/bin:$PATH

# Upgrade pip and install poetry
RUN pip install --upgrade pip

# Set Python-related environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install os dependencies for our mini vm
RUN apt-get update && apt-get install -y \
    # for postgres
    libpq-dev \
    # for Pillow
    libjpeg-dev \
    # for CairoSVG
    libcairo2 \
    # other
    gcc \
    && rm -rf /var/lib/apt/lists/*


# Create the mini vm's code directory
RUN mkdir -p /code

# Set the working directory to that same code directory
WORKDIR /code

# # Copy the poetry files to install depedencies and cache
COPY requirements.txt /code/

# # Export the dependencies to requirements.txt
# RUN poetry export -f requirements.txt --without-hashes -o proj_requirements.txt

# Install dependencies directly using pip
RUN pip install --no-cache-dir -r requirements.txt

# copy the project code into the container's working directory
COPY ./src /code

# Install dependencies via Poetry
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

ARG DJANGO_SECRET_KEY
ENV DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}

ARG DJANGO_DEBUG=0
ENV DJANGO_DEBUG=${DJANGO_DEBUG}

RUN python manage.py vendor_pull
RUN python manage.py collectstatic --noinput

# whitenoise -> object storage like s3 might be better


# set the Django default project name
ARG PROJ_NAME="myproject"

# create a bash script to run the Django project
# this script will execute at runtime when
# the container starts and the database is available
RUN printf "#!/bin/bash\n" > ./paracord_runner.sh && \
    printf "RUN_PORT=\"\${PORT:-8000}\"\n\n" >> ./paracord_runner.sh && \
    printf "python manage.py migrate --no-input\n" >> ./paracord_runner.sh && \
    printf "gunicorn ${PROJ_NAME}.wsgi:application --bind \"0.0.0.0:\$RUN_PORT\"\n" >> ./paracord_runner.sh

# make the bash script executable
RUN chmod +x paracord_runner.sh

# Clean up apt cache to reduce image size
RUN apt-get remove --purge -y \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Run the Django project via the runtime script
# when the container starts
CMD ./paracord_runner.sh