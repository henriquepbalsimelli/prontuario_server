FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ARG INSTALL_DEV=false

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app
COPY main.py ./main.py

RUN pip install --no-cache-dir --upgrade pip \
    && if [ "${INSTALL_DEV}" = "true" ]; then \
         pip install --no-cache-dir ".[dev]"; \
       else \
         pip install --no-cache-dir .; \
       fi

EXPOSE 8000

CMD ["uvicorn", "app.presentation.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
