FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt \
    && groupadd -g 10001 ranking \
    && useradd -u 10001 -g ranking -r -s /usr/sbin/nologin ranking \
    && mkdir /data \
    && chown ranking:ranking /data
COPY . .
USER ranking
CMD ["uvicorn", "webapp.server:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
