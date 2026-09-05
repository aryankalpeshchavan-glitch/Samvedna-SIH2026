FROM python:3.11-slim
WORKDIR /app
COPY ml/requirements.txt ./ml/requirements.txt
RUN pip install --no-cache-dir -r ml/requirements.txt
COPY ml/ ./ml/
COPY data/ ./data/
CMD ["python", "ml/ingest_to_backend.py"]
