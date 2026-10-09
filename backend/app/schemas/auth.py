"""Auth + user schemas. WHY: Pydantic rejects bad input before DB."""
from pydantic import BaseModel, EmailStr, Field


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    totp_code: str | None = None  # WHY: Admin MFA code sent with login if enabled


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    mfa_required: bool = False


class RefreshIn(BaseModel):
    refresh_token: str


class MFASetupOut(BaseModel):
    secret: str
    otpauth_url: str
    note: str = "SAMPLE: scan in authenticator app, then POST /mfa/verify"


class MFAVerifyIn(BaseModel):
    code: str = Field(min_length=6, max_length=8)


class RoleRequestIn(BaseModel):
    new_role: str = Field(pattern="^(Admin|Reviewer|Auditor|Vendor)$")
    reason: str = Field(min_length=5)


class DecideIn(BaseModel):
    approve: bool
    comments: str = ""
