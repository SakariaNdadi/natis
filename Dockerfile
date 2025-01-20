# Use the official Python 3 image as a base
FROM python:3

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing bytecode files (.pyc)
# PYTHONUNBUFFERED: Forces Python to output messages immediately (instead of buffering)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container to /code
WORKDIR /code

# Install dependencies
# Upgrade pip to the latest version
RUN pip install --upgrade pip
# Copy the requirements.txt file into the container
COPY requirements.txt /code/
# Install the dependencies specified in requirements.txt
RUN pip install -r requirements.txt

# Copy the entire Django project (current directory) into the container
COPY . /code/