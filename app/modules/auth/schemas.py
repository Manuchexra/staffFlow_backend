from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    identifier: str
    password: str

class VerifyOTPRequest(BaseModel):
    temp_auth_token: str  # Login qilgandan keyin yuborilan vaqtiy token
    otp: str               # Emailga yuborilgan 6 raqamli kod

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    device_id: str

class OTPResponse(BaseModel):
    temp_auth_token: str
    message: str
    expires_in_minutes: int