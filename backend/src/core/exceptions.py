"""
커스텀 예외 클래스 정의
HTTP 상태 코드와 메시지를 포함한 예외 처리
"""
from typing import Any, Dict, Optional


class APIException(Exception):
    """기본 API 예외 클래스"""

    def __init__(
        self,
        status_code: int,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DatabaseException(APIException):
    """데이터베이스 관련 예외"""

    def __init__(self, message: str = "데이터베이스 오류가 발생했습니다.", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=500, message=message, details=details)


class NotFoundError(APIException):
    """리소스를 찾을 수 없을 때 발생하는 예외"""

    def __init__(self, resource: str = "리소스", details: Optional[Dict[str, Any]] = None):
        message = f"{resource}를 찾을 수 없습니다."
        super().__init__(status_code=404, message=message, details=details)


class ValidationError(APIException):
    """데이터 검증 실패 예외"""

    def __init__(self, message: str = "데이터 검증에 실패했습니다.", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=422, message=message, details=details)


class ExternalAPIError(APIException):
    """외부 API 호출 실패 예외"""

    def __init__(
        self,
        api_name: str,
        message: str = "외부 API 호출에 실패했습니다.",
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details["api_name"] = api_name
        super().__init__(status_code=502, message=message, details=details)


class RateLimitError(APIException):
    """API 요청 제한 초과 예외"""

    def __init__(
        self,
        message: str = "API 요청 제한을 초과했습니다.",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(status_code=429, message=message, details=details)


class ModelInferenceError(APIException):
    """모델 추론 실패 예외"""

    def __init__(
        self,
        model_name: str,
        message: str = "모델 예측에 실패했습니다.",
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details["model_name"] = model_name
        super().__init__(status_code=500, message=message, details=details)


class BacktestError(APIException):
    """백테스팅 실패 예외"""

    def __init__(self, message: str = "백테스팅 실행에 실패했습니다.", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=500, message=message, details=details)


class UnauthorizedError(APIException):
    """인증 실패 예외"""

    def __init__(self, message: str = "인증에 실패했습니다.", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=401, message=message, details=details)


class ForbiddenError(APIException):
    """권한 부족 예외"""

    def __init__(self, message: str = "권한이 부족합니다.", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=403, message=message, details=details)
