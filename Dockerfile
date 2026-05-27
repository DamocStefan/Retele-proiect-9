FROM python:3.11-slim
RUN apt-get update && apt-get install -y nginx procps && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY nod_main.py .
COPY config_nod1.json .
COPY config_nod2.json .
COPY config_nod3.json .
ENV CONFIG_FILE=config_nod1.json
CMD ["python3", "nod_main.py"]
