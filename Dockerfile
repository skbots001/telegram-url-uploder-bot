# Use an official lightweight Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the bot files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port (not required for Telegram bots, but useful if needed)
EXPOSE 8080

# Start the bot
CMD ["python", "main.py"]
