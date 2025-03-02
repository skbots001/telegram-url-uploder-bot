FROM python:3.10

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install ffmpeg and other dependencies for moviepy
RUN apt-get update && apt-get install -y ffmpeg libxext6 libxrender1 libgl1

COPY . .

CMD ["python", "main.py"]
