FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY RandomCoffeBot.py ./

# Default data directory inside container. Override with DATA_DIR env if needed.
ENV DATA_DIR=/app/data

RUN mkdir -p /app/data

CMD ["python", "RandomCoffeBot.py"]
