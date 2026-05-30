FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        build-essential \
        curl \
        chromium \
        chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
COPY specs ./specs
COPY tests ./tests
COPY docker/constraints.txt ./docker/constraints.txt
COPY README.md ./

RUN pip install --upgrade pip \
    && pip install --index-url https://download.pytorch.org/whl/cpu "torch>=2.2,<3" \
    && pip install -c docker/constraints.txt .

COPY docker/start.sh ./docker/start.sh

EXPOSE 8000 8501

CMD ["bash", "docker/start.sh"]
