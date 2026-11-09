from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.core.config import settings
from app.core.deps import DB, CurrentUser
from app.core.security import (create_access_token, create_refresh_token, decode_token,
                               generate_reset_token, hash_password, hash_reset_token,
                               verify_password)
from app.models import PasswordResetToken, Role, User, utcnow
from app.schemas import (ChangePasswordIn, ForgotPasswordIn, Message, RefreshIn, RegisterIn,
                         ResetPasswordIn, Token, UserOut, UserUpdate)
from app.services.email import send_email

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=201, summary="Create a customer account")
def register(data: RegisterIn, db: DB):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(full_name=data.full_name, email=email, phone=data.phone,
                password_hash=hash_password(data.password), role=Role.customer)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token, summary="Login (username = email)")
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB):
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is disabled")
    return Token(access_token=create_access_token(user.id), refresh_token=create_refresh_token(user.id))


@router.post("/refresh", response_model=Token, summary="Get a new access token using a refresh token")
def refresh(data: RefreshIn, db: DB):
    user_id = decode_token(data.refresh_token, "refresh")
    user = db.get(User, user_id) if user_id else None
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    return Token(access_token=create_access_token(user.id), refresh_token=create_refresh_token(user.id))


@router.post("/forgot-password", response_model=Message, summary="Send a password reset link")
def forgot_password(data: ForgotPasswordIn, db: DB, bg: BackgroundTasks):
    generic = Message(message="If this email exists, a reset link has been sent")
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not user.is_active:
        return generic  # منكشفش إذا كان الإيميل موجود ولا لأ
    raw, hashed = generate_reset_token()
    db.add(PasswordResetToken(
        user_id=user.id, token_hash=hashed,
        expires_at=utcnow() + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)))
    db.commit()
    link = f"{settings.FRONTEND_URL}/reset-password?token={raw}"
    bg.add_task(send_email, user.email, "MOODS - Reset your password",
                f"Hi {user.full_name},\n\nReset your password using this link "
                f"(valid for {settings.RESET_TOKEN_EXPIRE_MINUTES} minutes):\n{link}\n")
    return generic


@router.post("/reset-password", response_model=Message, summary="Set a new password using the emailed token")
def reset_password(data: ResetPasswordIn, db: DB):
    rec = db.scalar(select(PasswordResetToken).where(
        PasswordResetToken.token_hash == hash_reset_token(data.token)))
    if not rec or rec.used or rec.expires_at < utcnow():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired reset token")
    user = db.get(User, rec.user_id)
    user.password_hash = hash_password(data.new_password)
    rec.used = True
    db.commit()
    return Message(message="Password has been reset successfully")


@router.post("/change-password", response_model=Message, summary="Change password while logged in")
def change_password(data: ChangePasswordIn, user: CurrentUser, db: DB):
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Old password is incorrect")
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return Message(message="Password changed successfully")


@router.get("/me", response_model=UserOut, summary="Current user profile")
def me(user: CurrentUser):
    return user


@router.patch("/me", response_model=UserOut, summary="Update my profile")
def update_me(data: UserUpdate, user: CurrentUser, db: DB):
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user
