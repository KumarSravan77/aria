import os
import random
import time
from fastapi import FastAPI, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="Sample Checkout API")
REQS = Counter("checkout_requests_total", "Total checkout requests", ["endpoint", "status"])
LAT = Histogram("checkout_request_duration_seconds", "Checkout request latency", ["endpoint"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "checkout-api"}

@app.get("/checkout")
def checkout():
    latency_ms = int(os.getenv("CHAOS_LATENCY_MS", "0"))
    error_rate = float(os.getenv("CHAOS_ERROR_RATE", "0"))
    start = time.time()
    if latency_ms > 0:
        time.sleep(latency_ms / 1000.0)
    if random.random() < error_rate:
        REQS.labels("/checkout", "500").inc()
        LAT.labels("/checkout").observe(time.time() - start)
        return Response(content='{"error":"simulated failure"}', media_type="application/json", status_code=500)
    REQS.labels("/checkout", "200").inc()
    LAT.labels("/checkout").observe(time.time() - start)
    return {"status": "success", "order_id": random.randint(1000, 9999)}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
