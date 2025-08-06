import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Google Gemini AI"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables")
            self.model = None
        else:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                logger.info("Gemini AI service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini AI: {e}")
                self.model = None
    
    async def analyze_market_data(self, sector: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market data using Gemini AI
        
        Args:
            sector: The sector to analyze
            market_data: Collected market data
            
        Returns:
            Analysis report with recommendations
        """
        start_time = datetime.utcnow()
        
        if not self.model:
            logger.warning("Gemini AI not available, returning mock analysis")
            return await self._generate_mock_analysis(sector, market_data)
        
        try:
            
            prompt = await self._create_analysis_prompt(sector, market_data)
            
            
            response = await self._generate_content_async(prompt)
            
            
            analysis = await self._parse_analysis_response(response, sector)
            
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            analysis["processing_time"] = processing_time
            
            logger.info(f"AI analysis completed for {sector} in {processing_time:.2f}s")
            return analysis
            
        except Exception as e:
            logger.error(f"AI analysis failed for {sector}: {e}")
            
            return await self._generate_mock_analysis(sector, market_data)
    
    async def _create_analysis_prompt(self, sector: str, market_data: Dict[str, Any]) -> str:
        """Create a comprehensive prompt for market analysis"""
        
        news_summary = "\n".join([
            f"- {item.get('title', 'N/A')}: {item.get('summary', 'N/A')}"
            for item in market_data.get('news', [])[:10] 
        ])
        
        financial_data = market_data.get('financial_data', {})
        market_trends = "\n".join([f"- {trend}" for trend in market_data.get('market_trends', [])])
        
        prompt = f"""
        As a financial market analyst, provide a comprehensive trade opportunities analysis for the {sector} sector in India.
        
        Based on the following market data:
        
        **Recent News and Developments:**
        {news_summary if news_summary.strip() else "No recent news available"}
        
        **Market Trends:**
        {market_trends if market_trends.strip() else "No specific trends identified"}
        
        **Financial Indicators:**
        {json.dumps(financial_data, indent=2) if financial_data else "No financial data available"}
        
        Please provide a detailed analysis in the following Markdown format:
        
        # {sector.title()} Sector Analysis - Trade Opportunities Report
        
        ## Executive Summary
        [Brief overview of current market conditions and key opportunities]
        
        ## Market Overview
        [Current state of the {sector} sector in India]
        
        ## Key Developments
        [Recent news and developments affecting the sector]
        
        ## Financial Analysis
        [Analysis of financial indicators and market performance]
        
        ## Trade Opportunities
        ### Short-term Opportunities (1-3 months)
        [List specific trading opportunities with rationale]
        
        ### Medium-term Opportunities (3-12 months)
        [List medium-term investment prospects]
        
        ### Long-term Outlook (1+ years)
        [Strategic investment considerations]
        
        ## Risk Assessment
        [Key risks and mitigation strategies]
        
        ## Recommendations
        [Specific actionable recommendations with risk ratings]
        
        ## Conclusion
        [Summary and final thoughts]
        
        Please ensure the analysis is:
        - Data-driven and objective
        - Specific to the Indian market context
        - Actionable with clear recommendations
        - Professional and comprehensive
        - Includes specific stock symbols or company names where relevant
        """
        
        return prompt
    
    async def _generate_content_async(self, prompt: str) -> str:
        """Generate content asynchronously using Gemini"""
        try:
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.model.generate_content(prompt)
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise
    
    async def _parse_analysis_response(self, response: str, sector: str) -> Dict[str, Any]:
        """Parse and structure the AI response"""
        try:
            
            recommendations = await self._extract_recommendations(response)
            
            
            confidence_score = await self._calculate_confidence_score(response)
            
            return {
                "report": response,
                "recommendations": recommendations,
                "confidence_score": confidence_score,
                "sector": sector,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to parse analysis response: {e}")
            return {
                "report": response,
                "recommendations": ["hold"],
                "confidence_score": 0.5,
                "sector": sector,
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def _extract_recommendations(self, text: str) -> List[str]:
        """Extract trading recommendations from the analysis"""
        recommendations = []
        text_lower = text.lower()
        
        
        if any(word in text_lower for word in ["buy", "purchase", "invest", "bullish"]):
            recommendations.append("buy")
        if any(word in text_lower for word in ["sell", "exit", "bearish", "decline"]):
            recommendations.append("sell")
        if any(word in text_lower for word in ["hold", "maintain", "wait", "cautious"]):
            recommendations.append("hold")
        
        return recommendations if recommendations else ["hold"]
    
    async def _calculate_confidence_score(self, text: str) -> float:
        """Calculate confidence score based on response quality"""
        try:
            
            score = 0.5  
            
            
            if len(text) > 1000:
                score += 0.2
            if "## " in text:  
                score += 0.1
            if any(word in text.lower() for word in ["data", "analysis", "market", "financial"]):
                score += 0.1
            if any(word in text.lower() for word in ["recommendation", "opportunity", "risk"]):
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception:
            return 0.5
    
    async def _generate_mock_analysis(self, sector: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a mock analysis when AI service is unavailable"""
        
        mock_report = f"""# {sector.title()} Sector Analysis - Trade Opportunities Report

## Executive Summary
This is a mock analysis for the {sector} sector as the AI service is currently unavailable. 
Please configure your GEMINI_API_KEY environment variable to enable full AI-powered analysis.

## Market Overview
The {sector} sector in India shows mixed signals based on available market data. 
Analysis of {len(market_data.get('news', []))} news items and market trends indicates 
moderate activity in this sector.

## Key Developments
Recent developments in the {sector} sector include various market movements and 
regulatory changes that may impact trading opportunities.

## Trade Opportunities
### Short-term Opportunities (1-3 months)
- Monitor sector performance for entry points
- Consider diversified exposure to sector leaders

### Medium-term Opportunities (3-12 months)
- Evaluate fundamental growth prospects
- Assess regulatory environment changes

## Risk Assessment
- Market volatility remains a key concern
- Sector-specific risks should be monitored

## Recommendations
- Maintain cautious approach until full analysis is available
- Consider professional consultation for investment decisions

## Conclusion
This mock analysis provides basic structure. Enable AI service for comprehensive insights.

*Note: This is a fallback analysis. Configure GEMINI_API_KEY for AI-powered insights.*
"""
        
        return {
            "report": mock_report,
            "recommendations": ["hold"],
            "confidence_score": 0.3,
            "sector": sector,
            "generated_at": datetime.utcnow().isoformat(),
            "processing_time": 0.1,
            "mock": True
        }
