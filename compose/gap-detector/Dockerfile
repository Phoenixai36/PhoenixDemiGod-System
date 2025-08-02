FROM python:3.11-slim

WORKDIR /app

COPY misc/src/core/gap_detection_system.py .

RUN pip install --no-cache-dir numpy torch

CMD ["python", "gap_detection_system.py"]