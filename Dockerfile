FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
COPY evaluation ./evaluation
COPY frontend ./frontend
COPY data ./data

RUN pip install --no-cache-dir ".[llm]"

EXPOSE 8000

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
