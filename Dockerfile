FROM python:3.12-slim
WORKDIR /app
COPY bot.py content.py ./
ENV PYTHONUNBUFFERED=1 DATABASE_PATH=/data/sbkh.sqlite3
RUN mkdir -p /data
VOLUME ["/data"]
CMD ["python", "bot.py"]
