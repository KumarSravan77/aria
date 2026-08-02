import os

os.environ.setdefault('API_AUTH_TOKEN', 'test-requester-token')
os.environ.setdefault('ALERTMANAGER_WEBHOOK_SECRET', 'test-alertmanager-secret')
os.environ.setdefault('API_USER_ID', 'test-sre')
os.environ.setdefault('API_USER_ROLE', 'sre')
os.environ.setdefault('API_USER_TEAM', 'platform')
os.environ.setdefault('API_AUTH_TOKENS', 'test-approver-token:test-commander:incident-commander:platform')

os.environ.setdefault('FALCO_WEBHOOK_SECRET', 'test-falco-secret')
