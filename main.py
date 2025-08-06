import os
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

from app.models import (
    AnalysisRequest, 
    AnalysisResponse, 
    UserCreate, 
    UserLogin, 
    Token,
    HealthCheck
)
from app.auth import authenticate_user, create_access_token, get_current_user, create_user
from app.services.gemini_service import GeminiService
from app.services.data_collector import DataCollector
from app.services.rate_limiter import RateLimiterService
from app.utils.exceptions import (
    APIException,
    AuthenticationException,
    RateLimitException,
    DataCollectionException
)


load_dotenv()


logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


limiter = Limiter(key_func=get_remote_address)


app = FastAPI(
    title="Trade Opportunities API",
    description="Analyze market data and provide trade opportunity insights for specific sectors in India",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


security = HTTPBearer()


gemini_service = GeminiService()
data_collector = DataCollector()
rate_limiter_service = RateLimiterService()

@app.exception_handler(APIException)
async def api_exception_handler(request, exc: APIException):
    """Handle custom API exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "type": exc.__class__.__name__}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "type": "ServerError"}
    )

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )

@app.post("/auth/register", response_model=Dict[str, str])
async def register(user: UserCreate):
    """Register a new user"""
    try:
        user_id = await create_user(user.username, user.email, user.password)
        return {"message": "User created successfully", "user_id": user_id}
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User registration failed"
        )

@app.post("/auth/login", response_model=Token)
async def login(user: UserLogin):
    """Authenticate user and return JWT token"""
    try:
        user_data = await authenticate_user(user.username, user.password)
        if not user_data:
            raise AuthenticationException("Invalid credentials")
        
        access_token = create_access_token(data={"sub": user_data["username"]})
        return Token(access_token=access_token, token_type="bearer")
    except AuthenticationException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/analyze/{sector}", response_model=AnalysisResponse)
@limiter.limit("10/minute")
async def analyze_sector(
    request,
    sector: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Analyze trade opportunities for a specific sector
    
    Args:
        sector: Name of the sector to analyze (e.g., pharmaceuticals, technology, agriculture)
        current_user: Authenticated user information
    
    Returns:
        Structured market analysis report
    """
    try:
        # Validate sector input
        if not sector or len(sector.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid sector name"
            )
        
        sector = sector.strip().lower()
        
        
        if not await rate_limiter_service.check_user_limit(current_user["username"]):
            raise RateLimitException("Rate limit exceeded for user")
        
        logger.info(f"Starting analysis for sector: {sector} by user: {current_user['username']}")
        
        
        try:
            market_data = await data_collector.collect_sector_data(sector)
        except Exception as e:
            logger.error(f"Data collection error: {e}")
            raise DataCollectionException("Failed to collect market data")
        
        
        try:
            analysis_report = await gemini_service.analyze_market_data(sector, market_data)
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            raise APIException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI analysis service temporarily unavailable"
            )
        
        
        await rate_limiter_service.record_usage(current_user["username"])
        
        
        response = AnalysisResponse(
            sector=sector,
            analysis_date=datetime.utcnow(),
            report=analysis_report["report"],
            confidence_score=analysis_report.get("confidence_score", 0.0),
            data_sources=market_data.get("sources", []),
            recommendations=analysis_report.get("recommendations", []),
            metadata={
                "user": current_user["username"],
                "processing_time": analysis_report.get("processing_time", 0),
                "data_points": len(market_data.get("news", [])),
            }
        )
        
        logger.info(f"Analysis completed for sector: {sector}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed due to internal error"
        )

@app.get("/sectors", response_model=Dict[str, Any])
async def get_supported_sectors(current_user: Dict = Depends(get_current_user)):
    """Get list of supported sectors for analysis"""
    sectors = [
        "pharmaceuticals",
        "technology", 
        "agriculture",
        "manufacturing",
        "textiles",
        "banking",
        "energy",
        "automotive",
        "real_estate",
        "telecommunications"
    ]
    
    return {
        "supported_sectors": sectors,
        "total_count": len(sectors),
        "description": "List of sectors available for trade opportunity analysis"
    }

@app.get("/usage", response_model=Dict[str, Any])
async def get_usage_stats(current_user: Dict = Depends(get_current_user)):
    """Get usage statistics for the current user"""
    stats = await rate_limiter_service.get_user_stats(current_user["username"])
    return {
        "user": current_user["username"],
        "requests_today": stats.get("requests_today", 0),
        "total_requests": stats.get("total_requests", 0),
        "remaining_requests": stats.get("remaining_requests", 0),
        "reset_time": stats.get("reset_time")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", 8000)),
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )
