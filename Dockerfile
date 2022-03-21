FROM python:3-alpine

WORKDIR /app/

RUN python -m pip install --no-cache-dir --upgrade pip==20.1

COPY run.py /

ENTRYPOINT ["python", "/run.py"]
