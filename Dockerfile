FROM python:3.10

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install ffmpeg for moviepy
RUN apt-get update && apt-get install -y ffmpeg

COPY . .

CMD ["python", "main.py"]
