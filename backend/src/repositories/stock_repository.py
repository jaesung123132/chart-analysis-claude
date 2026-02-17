"""
종목(Stock) 리포지토리
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.stock import Stock
import structlog

logger = structlog.get_logger()


class StockRepository:
    """종목 마스터 CRUD"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_ticker(self, ticker: str):
        """티커로 종목 조회"""
        result = await self.db.execute(
            select(Stock).where(Stock.ticker == ticker.upper())
        )
        return result.scalar_one_or_none()

    async def create(self, ticker: str, name: str, sector: str = None, market: str = "US"):
        """종목 생성"""
        stock = Stock(
            ticker=ticker.upper(),
            name=name,
            sector=sector,
            market=market
        )
        self.db.add(stock)
        await self.db.flush()
        logger.info("종목 생성", ticker=ticker)
        return stock

    async def get_or_create(self, ticker: str, name: str = None, market: str = "US"):
        """종목 조회 또는 생성"""
        stock = await self.get_by_ticker(ticker)
        if stock is None:
            stock = await self.create(
                ticker=ticker,
                name=name or ticker,
                market=market
            )
        return stock
