# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файл с зависимостями в рабочую директорию
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Создаем директорию для хранения данных
RUN mkdir output

# Копируем весь код проекта в рабочую директорию
COPY . .

# Указываем команду для запуска бота при старте контейнера
CMD ["python", "telegram_bot/bot.py"]
