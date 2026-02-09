FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies including ffmpeg and audio libs
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ffmpeg \
       build-essential \
       libsndfile1 \
       git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (use PyTorch CPU wheels index)
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip setuptools wheel \
    && PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu pip install -r /app/requirements.txt

# Copy application code
COPY . /app

RUN mkdir -p /app/uploads

EXPOSE 10000

CMD ["sh","-c","gunicorn app:app --bind 0.0.0.0:${PORT:-10000}"]
