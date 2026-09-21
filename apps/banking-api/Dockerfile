FROM python:3.11-slim
ARG PIP_INDEX_URL="https://pypi.org/simple"
ARG PIP_TRUSTED_HOST=""
ENV PIP_INDEX_URL=${PIP_INDEX_URL} PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST}
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
USER 65532:65532
EXPOSE 9200
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9200"]
