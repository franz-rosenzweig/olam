# Olam in a container. The data folder (the index, the downloads, the password) is the volume at /data.
FROM python:3.14-slim
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 1000 --create-home olam && mkdir /data && chown olam /data
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY olam olam
COPY web web
COPY lessons lessons
USER olam
ENV OLAM_DATA=/data OLAM_HOSTS=0.0.0.0 OLAM_PORT=8462 PYTHONUNBUFFERED=1
VOLUME /data
EXPOSE 8462
ENTRYPOINT ["python", "-m", "olam.cli"]
CMD ["serve"]
