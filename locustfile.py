from locust import HttpUser, task, between
import hmac
import hashlib
import json

class WebhookUser(HttpUser):
    wait_time = between(0.01, 0.05)
    
    @task
    def send_webhook(self):
        import uuid
        tx_hash = str(uuid.uuid4())
        payload = {
            "tx_hash": tx_hash,
            "wallet_address": "test_wallet",
            "time": "2024-01-01T00:00:00Z",
            "payload": "{}"
        }
        payload_str = json.dumps(payload)
        # Using default ton webhook secret from config
        sig = hmac.new(b'test_ton_secret', payload_str.encode(), hashlib.sha256).hexdigest()
        self.client.post("/gateway/ton", payload_str, headers={"X-Tonapi-Signature": sig, "Content-Type": "application/json"})
