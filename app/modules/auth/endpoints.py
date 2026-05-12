from fastapi import APIRouter, Depends, status, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.modules.auth.schemas import (
    LoginRequest, TokenResponse, VerifyOTPRequest, 
    OTPResponse, ErrorResponse
)
from app.modules.auth.service import AuthService
from app.core.deps import security, get_current_user
from app.core.device_utils import get_or_create_device_id
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post(
    "/login",
    response_model=TokenResponse | OTPResponse,
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Invalid credentials or authentication failed"
        },
        423: {
            "model": ErrorResponse,
            "description": "Account locked due to too many failed attempts"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error"
        }
    },
    summary="[Auth] User Login",
    description="Authenticate user with phone number or email and password."
)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login endpoint with JWT authentication.
    
    Requirements:
    - identifier: Phone number or email (e.g., "+998901234567" or "user@example.com")
    - password: At least 8 characters
    
    Returns:
    - access_token: JWT token for API requests (1 hour validity)
    - refresh_token: JWT token to get new access token (30 days validity)
    - user_id: Authenticated user ID
    - device_id: Device identifier for tracking
    """
    start_time = time.time()
    
    try:
        # Get device ID from user agent and headers
        user_agent = request.headers.get("user-agent", "")
        device_id = get_or_create_device_id(None, user_agent)
        
        # Authenticate user and generate tokens
        result = await AuthService.authenticate(
            db,
            login_data.identifier,
            login_data.password,
            device_id
        )
        
        response_time = time.time() - start_time
        logger.info(f"Login successful for {login_data.identifier} - Response time: {response_time:.2f}s")
        
        if result.get("requires_otp"):
            # OTP verification required (for new devices)
            return OTPResponse(
                temp_auth_token=result["temp_auth_token"],
                message=result["message"],
                expires_in_minutes=result["expires_in_minutes"],
                requires_otp=True
            )
        else:
            # Direct token response (for known devices)
            return TokenResponse(
                access_token=result["access_token"],
                refresh_token=result["refresh_token"],
                user_id=result["user_id"],
                device_id=result["device_id"],
                expires_in=result["expires_in"]
            )
            
    except HTTPException as e:
        response_time = time.time() - start_time
        logger.warning(f"Login failed for {login_data.identifier} - Status: {e.status_code} - Time: {response_time:.2f}s")
        raise
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(f"Unexpected error during login - Time: {response_time:.2f}s - Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable"
        )


@router.post(
    "/verify-otp",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired OTP"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="[Auth] Verify OTP",
    description="Complete login process by verifying OTP code sent to registered email"
)
async def verify_otp(
    otp_request: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify OTP code and complete authentication.
    
    Required for new device logins. OTP sent to registered email address.
    
    Parameters:
    - temp_auth_token: Temporary token received from login response
    - otp: 6-digit code sent to email
    """
    try:
        result = await AuthService.verify_otp_and_complete_login(
            db,
            otp_request.temp_auth_token,
            otp_request.otp
        )
        
        logger.info(f"OTP verification successful for user {result['user_id']}")
        
        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            user_id=result["user_id"],
            device_id=result["device_id"],
            expires_in=3600
        )
    except HTTPException as e:
        logger.warning(f"OTP verification failed - Status: {e.status_code}")
        raise
    except Exception as e:
        logger.error(f"OTP verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OTP verification failed"
        )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="[Auth] User Logout",
    description="Logout user and invalidate access token"
)
async def logout(
    credentials = Depends(security),
    current_user = Depends(get_current_user)
):
    """
    Logout endpoint - invalidates the access token.
    
    After logout, the token cannot be used for API requests.
    """
    try:
        token = credentials.credentials
        result = await AuthService.logout(token)
        
        logger.info(f"User {current_user.id} logged out successfully")
        
        return result
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )