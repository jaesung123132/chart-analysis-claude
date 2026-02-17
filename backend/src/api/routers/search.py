"""
종목 검색 API 라우터 (한글/영문 통합)
"""
from fastapi import APIRouter, Query
from datetime import datetime
from ...schemas.stock import APIResponse
from ...services.stock_search_service import StockSearchService
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/search", tags=["search"])

# 검색 서비스 초기화 (앱 시작 시 1회 로드)
search_service = StockSearchService()


@router.get("")
async def search_stocks(
    q: str = Query(..., description="검색어 (한글 또는 영문)", example="테슬라"),
    limit: int = Query(default=10, ge=1, le=30, description="최대 결과 수")
):
    """
    종목 검색 (한글/영문 자동완성)

    - **q**: 검색어 (예: 테슬라, TSLA, Tesla, 슈퍼마이크로)
    - **limit**: 최대 결과 수 (기본 10개)
    """
    results = search_service.search(q, limit)

    return APIResponse(
        success=True,
        data={
            "query": q,
            "results": results,
            "totalCount": len(results)
        },
        message=f"검색 완료: {len(results)}개 종목",
        timestamp=datetime.utcnow()
    )
