# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expose port 8080 (for dummy health check)
EXPOSE 8080

# Start a dummy HTTP server for health checks & run the bot
CMD python -m http.server 8080 & python bot.py
