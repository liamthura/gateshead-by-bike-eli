# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory in the container
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy the application code
COPY main.py .

# Copy the database CSV files
COPY db/ ./db/

# Expose the port the app runs on
EXPOSE 3000

# Set environment variable to ensure Python output is sent straight to terminal
ENV PYTHONUNBUFFERED=1

# Run the application
# Note: The application uses host='localhost' in main.py which needs to be changed to '0.0.0.0' for Docker
# Using sed to modify the host at runtime to avoid changing the source code
CMD ["/bin/sh", "-c", "sed -i \"s/host='localhost'/host='0.0.0.0'/g\" main.py && python main.py"]
