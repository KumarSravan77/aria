#!/usr/bin/env python3
import hashlib
import hmac
import os
import sys
import time
import uuid

if len(sys.argv) < 3:
    print("usage: hmac_sign.py <secret-env-name> <payload-file>", file=sys.stderr)
    sys.exit(2)

secret = os.getenv(sys.argv[1])
if not secret:
    print(f"missing env var {sys.argv[1]}", file=sys.stderr)
    sys.exit(2)

payload = open(sys.argv[2], "rb").read()
timestamp = str(int(time.time()))
nonce = str(uuid.uuid4())
signed = timestamp.encode() + b"." + nonce.encode() + b"." + payload
signature = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()

print(f"X-Timestamp: {timestamp}")
print(f"X-Nonce: {nonce}")
print(f"X-Incident-Signature: sha256={signature}")
