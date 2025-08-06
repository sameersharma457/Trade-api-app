from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, EmailStr, Field, validator


class UserCreate(BaseModel):
    """Model for user registration"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('Username must contain only alphanumeric characters')
        return v.lower()


class UserLogin(BaseModel):
    """Model for user login"""
    username: str
    password: str


class Token(BaseModel):
    """JWT token response model"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data model"""
    username: Optional[str] = None


class User(BaseModel):
    """User model"""
    username: str
    email: str
    is_active: bool = True
    created_at: datetime


class AnalysisRequest(BaseModel):
    """Request model for sector analysis"""
    sector: str = Field(..., min_length=2, max_length=100)
    
    @validator('sector')
    def validate_sector(cls, v):
        
        import re
        cleaned = re.sub(r'[^a-zA-Z0-9\s_-]', '', v)
        if not cleaned.strip():
            raise ValueError('Invalid sector name')
        return cleaned.strip().lower()


class AnalysisResponse(BaseModel):
    """Response model for sector analysis"""
    sector: str
    analysis_date: datetime
    report: str = Field(..., description="Markdown formatted analysis report")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    data_sources: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any] = {}


class HealthCheck(BaseModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    version: str


class MarketData(BaseModel):
    """Market data collection model"""
    sector: str
    news: List[Dict[str, Any]] = []
    financial_data: Dict[str, Any] = {}
    market_trends: List[str] = []
    sources: List[str] = []
    collected_at: datetime


class RateLimitInfo(BaseModel):
    """Rate limit information model"""
    requests_remaining: int
    reset_time: datetime
    limit: int
    window: int


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None
