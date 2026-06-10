from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class WebhookPayloadBase(BaseModel):
    tx_hash: str = Field(..., description="Unique transaction hash on the blockchain")
    wallet_address: str = Field(..., description="The wallet address being monitored")
    time: datetime = Field(..., description="Timestamp of transaction execution")
    payload: str = Field(..., description="Raw transaction hex or JSON string")

class TonWebhookPayload(WebhookPayloadBase):
    logical_time: int = Field(..., description="Logical time (lt) used in TON for message ordering")
    trace_id: Optional[str] = Field(None, description="Logical trace ID for async message chaining")

class SolWebhookPayload(WebhookPayloadBase):
    signature_ver: Optional[str] = Field(None, description="Signature key or proof")

class EvmWebhookPayload(WebhookPayloadBase):
    block_number: Optional[int] = Field(None, description="Block number containing transaction")
