# Use Python image
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy files
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ .

# Run app
CMD ["python", "app.py"]