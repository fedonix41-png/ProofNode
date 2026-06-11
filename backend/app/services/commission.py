import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from backend.app.db import db

logger = logging.getLogger(__name__)

async def aggregate_daily_commission():
    """
    Aggregates daily 5% commission from subscription payments and creates a payout record.
    """
    # Assuming yesterday's period
    now = datetime.now(timezone.utc)
    period_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
    period_start = period_end - timedelta(days=1)
    
    async for conn in db.get_connection():
        # Calculate total commission from tariffs paid in crypto over the last day
        # In a real system, we'd query actual payment records. We will query subscriptions joined with tariffs.
        row = await conn.fetchrow(
            """
            SELECT COALESCE(SUM(t.price_crypto), 0) as total_volume
            FROM subscriptions s
            JOIN tariffs t ON s.tariff_id = t.id
            WHERE s.created_at >= $1 AND s.created_at < $2
            """,
            period_start, period_end
        )
        
        total_volume = row["total_volume"] if row and row["total_volume"] else Decimal(0)
        commission_amount = total_volume * Decimal("0.05")
        
        if commission_amount > 0:
            await schedule_payout(conn, period_start, period_end, total_volume, commission_amount)
            logger.info(f"Aggregated daily commission: {commission_amount} for volume {total_volume}")
        else:
            logger.info("No commission to aggregate for yesterday.")

async def schedule_payout(conn, period_start: datetime, period_end: datetime, total_volume: Decimal, commission_amount: Decimal):
    """
    Create a pending commission_payouts record.
    """
    await conn.execute(
        """
        INSERT INTO commission_payouts (period_start, period_end, total_volume, commission_amount, status)
        VALUES ($1, $2, $3, $4, 'PENDING')
        """,
        period_start, period_end, total_volume, commission_amount
    )
