FROM python:3.10-slim

# Install system dependencies (FFmpeg for video, ImageMagick for subtitles)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick security policy to allow TextClip to render words
RUN sed -i 's/<policy domain="path" rights="none" pattern="@\*"//g' /etc/ImageMagick-*/policy.xml

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Start the API server
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-10000}"]
