# Базовый образ с Python
FROM python:3.9-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Устанавливаем системные зависимости (если нужны)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта
COPY src/ ./src/
COPY models/ ./models/
COPY data/ ./data/
COPY config.ini .

# Открываем порт для API
EXPOSE 8000

# Команда для запуска API
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]