from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    """Login endpoint request with phone or email"""
    identifier: str = Field(..., min_length=1, description="Phone number or email address")
    password: str = Field(..., min_length=8, description="User password")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class VerifyOTPRequest(BaseModel):
    """OTP verification request"""
    temp_auth_token: str = Field(..., description="Temporary auth token from login response")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")

class TokenResponse(BaseModel):
    """Successful authentication response"""
    access_token: str = Field(..., description="JWT access token for API requests")
    refresh_token: str = Field(..., description="JWT refresh token for getting new access token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: int = Field(..., description="Authenticated user ID")
    device_id: str = Field(..., description="Device identifier")
    expires_in: int = Field(..., description="Access token expiry in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user_id": 1,
                "device_id": "device_abc123",
                "expires_in": 3600
            }
        }

class OTPResponse(BaseModel):
    """Response when OTP verification is required"""
    temp_auth_token: str = Field(..., description="Temporary token for OTP verification")
    message: str = Field(..., description="User-friendly message")
    expires_in_minutes: int = Field(..., description="OTP expiry time in minutes")
    requires_otp: bool = Field(default=True, description="Flag indicating OTP is required")
    
    class Config:
        schema_extra = {
            "example": {
                "temp_auth_token": "temp_auth:1:device_abc123",
                "message": "OTP code has been sent to your email. Please verify.",
                "expires_in_minutes": 10,
                "requires_otp": True
            }
        }

class LoginResponse(BaseModel):
    """Union-like response for login endpoint"""
    pass

class ErrorResponse(BaseModel):
    """Error response"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code for client handling")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "detail": "Invalid credentials",
                "error_code": "INVALID_CREDENTIALS",
                "timestamp": "2024-05-12T10:30:00Z"
            }
        }