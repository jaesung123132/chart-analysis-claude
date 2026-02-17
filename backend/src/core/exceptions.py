"""
커스텀 예외 클래스
"""
from typing import Any, Optional


class APIException(Exception):
    """기본 API 예외"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class StockNotFoundException(APIException):
    """종목을 찾을 수 없음"""
    
    def __init__(self, ticker: str):
        super().__init__(
            message=f"종목을 찾을 수 없습니다: {ticker}",
            status_code=404,
            details={"ticker": ticker}
        )


class DataFetchException(APIException):
    """데이터 조회 실패"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=f"데이터 조회 실패: {message}",
            status_code=503,
            details=details
        )


class ValidationException(APIException):
    """입력 데이터 검증 실패"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=f"검증 실패: {message}",
            status_code=422,
            details=details
        )
