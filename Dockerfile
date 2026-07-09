FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GDAL_DISABLE_READDIR_ON_OPEN=EMPTY_DIR \
    CPL_VSIL_CURL_ALLOWED_EXTENSIONS=.tif,.tiff \
    TITILER_CONFIG=/config/config.json

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app
COPY config.example.json /config/config.json

RUN pip install --no-cache-dir .

EXPOSE 8000

VOLUME ["/config"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
