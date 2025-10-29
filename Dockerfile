# Используем стабильный образ Python 3.11
FROM python:3.11-slim

# Рабочая директория
WORKDIR /app

# Копируем файлы проекта
COPY . /app

# Устанавливаем зависимости (кэшируем установку)
RUN pip install --upgrade pip
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# Экспорт переменных окружения (опционально)
ENV PYTHONUNBUFFERED=1

# Команда по умолчанию
CMD ["python", "main.py"]
