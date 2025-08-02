FROM python:3.9

WORKDIR /app

COPY misc/src/core/recurrent_processor.py .

RUN pip install torch numpy

CMD ["python", "recurrent_processor.py"]