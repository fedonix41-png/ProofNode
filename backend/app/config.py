from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # PostgreSQL / TimescaleDB
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgrespassword", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="proofnode", alias="POSTGRES_DB")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")

    # RabbitMQ
    rabbitmq_host: str = Field(default="localhost", alias="RABBITMQ_HOST")
    rabbitmq_port: int = Field(default=5672, alias="RABBITMQ_PORT")
    rabbitmq_user: str = Field(default="guest", alias="RABBITMQ_USER")
    rabbitmq_password: str = Field(default="guest", alias="RABBITMQ_PASSWORD")

    # Redis
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")

    # Webhook Secrets (for signature validation)
    webhook_secret_ton: str = Field(default="test_ton_secret", alias="WEBHOOK_SECRET_TON")
    webhook_secret_sol: str = Field(default="test_sol_secret", alias="WEBHOOK_SECRET_SOL")
    webhook_secret_evm: str = Field(default="test_evm_secret", alias="WEBHOOK_SECRET_EVM")
    alchemy_webhook_secret: str = Field(default="alchemy_test_secret", alias="ALCHEMY_WEBHOOK_SECRET")
    helius_webhook_secret: str = Field(default="helius_test_secret", alias="HELIUS_WEBHOOK_SECRET")
    tonapi_webhook_secret: str = Field(default="tonapi_test_secret", alias="TONAPI_WEBHOOK_SECRET")

    # RPC URLs
    solana_rpc_url: str = Field(default="https://api.mainnet-beta.solana.com", alias="SOLANA_RPC_URL")
    base_rpc_url: str = Field(default="https://mainnet.base.org", alias="BASE_RPC_URL")
    ton_rpc_url: str = Field(default="https://toncenter.com/api/v2/jsonRPC", alias="TON_RPC_URL")

    # Platform
    platform_treasury_address: str = Field(default="EQ_PLATFORM_TREASURY_ADDRESS", alias="PLATFORM_TREASURY_ADDRESS")

    # FastAPI settings
    env: str = Field(default="development", alias="ENV")

    # Telegram Bot Settings
    bot_token: str = Field(default="mock_token", alias="BOT_TOKEN")
    channel_id: int = Field(default=-10012345678, alias="CHANNEL_ID")

    # KMS Encryption settings
    kms_master_key: str = Field(default="test_kms_master_key_dev_placeholder", alias="KMS_MASTER_KEY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def database_url_async(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def database_url_sync(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def rabbitmq_url(self) -> str:
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}/"

settings = Settings()
