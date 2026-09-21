FROM python:3.11-slim
ARG PIP_INDEX_URL="https://pypi.org/simple"
ARG PIP_TRUSTED_HOST=""
ARG INSTALL_LOCAL_EMBEDDINGS="false"
ENV PIP_INDEX_URL=${PIP_INDEX_URL} PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST}
WORKDIR /app

RUN useradd --create-home --uid 10001 aria
ENV PYTHONPATH=/app
COPY server/requirements.txt /app/server/requirements.txt
RUN grep -v '^sentence-transformers==' /app/server/requirements.txt > /tmp/runtime-requirements.txt \
    && pip install --no-cache-dir -r /tmp/runtime-requirements.txt \
    && if [ "$INSTALL_LOCAL_EMBEDDINGS" = "true" ]; then pip install --no-cache-dir sentence-transformers==3.3.1; fi
COPY server /app/server
COPY docs /app/docs
COPY scripts /app/scripts

RUN chown -R aria:aria /app

USER 10001
EXPOSE 8080
CMD ["uvicorn", "server.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
