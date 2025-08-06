from fastapi import HTTPException


class APIException(HTTPException):
    """Base API exception"""
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class AuthenticationException(APIException):
    """Authentication related exceptions"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=401, detail=detail)


class AuthorizationException(APIException):
    """Authorization related exceptions"""
    def __init__(self, detail: str = "Access denied"):
        super().__init__(status_code=403, detail=detail)


class RateLimitException(APIException):
    """Rate limiting exceptions"""
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(status_code=429, detail=detail)


class ValidationException(APIException):
    """Input validation exceptions"""
    def __init__(self, detail: str = "Invalid input"):
        super().__init__(status_code=400, detail=detail)


class DataCollectionException(APIException):
    """Data collection related exceptions"""
    def __init__(self, detail: str = "Data collection failed"):
        super().__init__(status_code=503, detail=detail)


class AIServiceException(APIException):
    """AI service related exceptions"""
    def __init__(self, detail: str = "AI service unavailable"):
        super().__init__(status_code=503, detail=detail)


class ResourceNotFoundException(APIException):
    """Resource not found exceptions"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)
