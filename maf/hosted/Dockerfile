# Build from the repo root (pf_jobpack must be in the context):
#   docker build -f maf/hosted/Dockerfile -t tco-slice2-host .
FROM python:3.11-slim

WORKDIR /app

COPY pf_jobpack /app/pf_jobpack
COPY maf /app/maf

RUN pip install --no-cache-dir -r /app/maf/hosted/requirements.txt

ENV PYTHONPATH=/app
EXPOSE 8088

CMD ["python", "-m", "maf.host", "--serve"]
