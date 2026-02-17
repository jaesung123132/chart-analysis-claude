"""
주식 검색 서비스 (한글/영문 통합 검색)
"""
import json
import os
from typing import List, Dict
import structlog

logger = structlog.get_logger()


class StockSearchService:
    """한글/영문 종목 검색 서비스"""

    def __init__(self):
        self._mappings: List[Dict] = []
        self._load_mappings()
        logger.info("StockSearchService 초기화 완료", count=len(self._mappings))

    def _load_mappings(self):
        """JSON 매핑 파일 로드 (앱 시작 시 1회)"""
        try:
            data_path = os.path.join(os.path.dirname(__file__), "../data/stock_mappings.json")
            data_path = os.path.normpath(data_path)
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._mappings = data.get("stocks", [])
        except Exception as e:
            logger.error("매핑 파일 로드 실패", error=str(e))
            self._mappings = []

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        한글/영문 통합 검색

        우선순위:
        1. ticker 완전 매칭
        2. nameKr 시작 매칭
        3. nameEn 시작 매칭
        4. nameKr/nameEn/aliases 부분 매칭
        """
        if not query or not query.strip():
            return []

        q = query.strip().lower().replace(" ", "")
        results = []

        # 우선순위별로 결과 수집
        tier1, tier2, tier3, tier4 = [], [], [], []

        for stock in self._mappings:
            ticker = stock["ticker"].lower()
            name_kr = stock["nameKr"].lower().replace(" ", "")
            name_en = stock["nameEn"].lower().replace(" ", "")
            aliases = [a.lower().replace(" ", "") for a in stock.get("aliases", [])]

            # 1. ticker 완전 매칭
            if ticker == q:
                tier1.append(stock)
            # 2. nameKr 시작 매칭
            elif name_kr.startswith(q):
                tier2.append(stock)
            # 3. nameEn 시작 매칭 또는 ticker 시작 매칭
            elif name_en.startswith(q) or ticker.startswith(q):
                tier3.append(stock)
            # 4. 부분 매칭 (nameKr, nameEn, aliases)
            elif q in name_kr or q in name_en or any(q in a for a in aliases):
                tier4.append(stock)

        # 중복 제거 후 우선순위 순으로 병합
        seen = set()
        for stock in tier1 + tier2 + tier3 + tier4:
            if stock["ticker"] not in seen:
                seen.add(stock["ticker"])
                results.append({
                    "ticker": stock["ticker"],
                    "nameKr": stock["nameKr"],
                    "nameEn": stock["nameEn"],
                    "market": stock["market"]
                })
            if len(results) >= limit:
                break

        logger.info("종목 검색 완료", query=query, count=len(results))
        return results
