import asyncio
import logging
import signal
from decimal import Decimal
from datetime import datetime

from backend.app.db import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def compute_and_upsert_stats():
    async for conn in db.get_connection():
        # Get all trader profiles
        profiles = await conn.fetch("SELECT id FROM trader_profiles")
        for profile in profiles:
            profile_id = profile["id"]
            
            # Fetch all wallets for this trader
            wallets = await conn.fetch(
                "SELECT address, blockchain FROM trader_wallets WHERE trader_profile_id = $1", 
                profile_id
            )
            
            if not wallets:
                continue
                
            # Compute stats (dummy calculation based on transactions)
            # In a real app, this would correctly sequence buy/sells for a given token
            # For this MVP, we will do a simple aggregation of amounts
            
            total_wins = 0
            total_trades = 0
            cumulative_profit_usd = Decimal(0)
            max_drawdown = Decimal(0)
            
            for w in wallets:
                address = w["address"]
                # Fetch recent transactions
                txs = await conn.fetch(
                    "SELECT tx_type, usd_value FROM wallet_transactions WHERE wallet_address = $1",
                    address
                )
                
                # Simplified calculation: 
                # BUY decreases profit (invested), SELL increases profit (returned)
                # If SELL > matching BUY, it's a win.
                # Here we just mock stats for demonstration
                if txs:
                    for tx in txs:
                        if tx["tx_type"] == "SELL" and tx["usd_value"]:
                            total_trades += 1
                            if tx["usd_value"] > 0: # Mock condition
                                total_wins += 1
                            cumulative_profit_usd += tx["usd_value"]
                        elif tx["tx_type"] == "BUY" and tx["usd_value"]:
                            cumulative_profit_usd -= tx["usd_value"]
                            
            if total_trades > 0:
                winrate = Decimal(total_wins) / Decimal(total_trades) * Decimal(100)
            else:
                winrate = Decimal(0)
                
            daily_roi = Decimal("5.0") # Mock
            cumulative_roi = Decimal("15.0") # Mock
            drawdown = Decimal("10.0") # Mock
            
            # Upsert into trader_pnl_history
            now = datetime.utcnow()
            await conn.execute(
                """
                INSERT INTO trader_pnl_history (time, trader_profile_id, daily_roi, cumulative_roi, winrate, drawdown)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (time, trader_profile_id) DO UPDATE SET
                    daily_roi = EXCLUDED.daily_roi,
                    cumulative_roi = EXCLUDED.cumulative_roi,
                    winrate = EXCLUDED.winrate,
                    drawdown = EXCLUDED.drawdown
                """,
                now, profile_id, daily_roi, cumulative_roi, winrate, drawdown
            )
            logger.info(f"Updated stats for profile {profile_id}: winrate={winrate}%")

async def main() -> None:
    await db.connect()
    
    logger.info("Stats Worker started.")
    
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    
    def shutdown_handler():
        logger.info("Received termination signal. Stopping worker...")
        stop_event.set()
        
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown_handler)
        
    while not stop_event.is_set():
        try:
            await compute_and_upsert_stats()
        except Exception as e:
            logger.error(f"Error computing stats: {e}")
            
        # Run every 10 minutes
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=600)
        except asyncio.TimeoutError:
            pass
            
    await db.disconnect()
    logger.info("Stats Worker shut down successfully.")

if __name__ == "__main__":
    asyncio.run(main())
