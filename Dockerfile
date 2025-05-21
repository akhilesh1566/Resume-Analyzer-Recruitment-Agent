# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir reduces image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Make port 8501 available to the world outside this container
# Streamlit default port is 8501.
EXPOSE 8501

# Command to run the Streamlit application
# Cloud Run will inject a PORT environment variable. We tell Streamlit to use it.
# --server.headless "true" is good practice for containers.
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"]