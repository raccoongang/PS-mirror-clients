FROM python:3-slim

ENV PYTHONUNBUFFERED True
WORKDIR /mirror-clients
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ scripts/ ./
ENTRYPOINT ["python", "-m", "mirror_clients.sync_session"]
