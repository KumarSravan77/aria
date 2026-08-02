FROM python:3.11-slim
WORKDIR /app
ENV PYTHONPATH=/app
COPY server/requirements.txt /app/server/requirements.txt
RUN pip install --no-cache-dir -r /app/server/requirements.txt
COPY server /app/server
COPY docs /app/docs
COPY scripts /app/scripts
EXPOSE 8080
CMD ["uvicorn", "server.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
