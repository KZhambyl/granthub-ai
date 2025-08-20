from sqlalchemy.ext.asyncio.session import AsyncSession
from fastapi import APIRouter, Depends, status, BackgroundTasks
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from .schemes import UserCreateModel, UserLoginModel, EmailModel, PasswordResetRequestModel, PasswordResetConfirmModel
from .service import UserService
from .utils import (
    create_access_token,
    verify_password,
    generate_password_hash,
    create_url_safe_token,
    decode_url_safe_token
)
from .dependencies import RefreshTokenBearer, AccessTokenBearer, get_current_user, RoleChecker
from app.db.main import get_session
from app.db.redis import add_jti_to_blocklist
from app.middlewares.mail import mail, create_message
from app.core.config import settings
from datetime import timedelta, datetime
from app.celery_tasks import send_email


auth_router = APIRouter()
user_service = UserService()
role_checker = RoleChecker(['admin', 'user'])

REFRESH_TOKEN_EXPIRY=2


@auth_router.post('/send_mail')
async def send_mail(emails: EmailModel):
    emails = emails.addresses

    html = "<h1>Welcome to the app</h1>"
    subject = "Welcome to our app"

    send_email.delay(emails, subject, html)

    return {"message":"Email has been sent successfully"}




@auth_router.post('/signup', status_code=status.HTTP_201_CREATED)
async def create_user_account(user_data: UserCreateModel, bg_tasks: BackgroundTasks, session: AsyncSession = Depends(get_session)):
    email = user_data.email

    user_exists = await user_service.user_exists(email, session)

    if user_exists:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User with this email already exists")

    new_user = await user_service.create_user(user_data, session)

    token = create_url_safe_token({"email":email})

    link = f"http://{settings.DOMAIN}/api/v1/auth/verify/{token}"

    html = f"""
    <h1>Verify your Email</h1>
    <p>Please click this <a href="{link}">link</a> to verify your email</p>
    """     

    emails = [email]
    subject ="Verify your email"

    send_email.delay(emails, subject, html)

    return {
        "message":"Account Created! Check email to verify your account",
        "user": new_user
    }

@auth_router.get('/verify/{token}')
async def verify_user_account(token: str, session: AsyncSession = Depends(get_session)):

    token_data = decode_url_safe_token(token)

    user_email = token_data.get('email')

    if user_email:
        user = await user_service.get_user_by_email(user_email, session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message":"User with such email address not found"}
            )
        
        await user_service.update_user(user, {'is_verified': True}, session)

        return JSONResponse(content={
            "message":"Account verified successfully",
        }, status_code=status.HTTP_200_OK)
    
    return JSONResponse(
        content={"message":"Error occured during verification"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

@auth_router.post('/login', status_code=status.HTTP_200_OK)
async def login_users(login_data: UserLoginModel, session: AsyncSession = Depends(get_session)):
    email = login_data.email
    password = login_data.password

    user = await user_service.get_user_by_email(email, session)

    if user is not None:
        password_valid = verify_password(password, user.password_hash)

        if password_valid:
            access_token = create_access_token(
                user_data={
                    'email': user.email,
                    'user_uid': str(user.uid),
                    'role' : user.role
                }
            )

            refresh_token = create_access_token(
                user_data={
                    'email': user.email,
                    'user_uid': str(user.uid)
                },
                refresh = True,
                expiry=timedelta(days=REFRESH_TOKEN_EXPIRY)
            )


            return JSONResponse(
                content={
                    "message":"Login successful",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {
                        "email": user.email,
                        "uid": str(user.uid)
                    }
                }
            )
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid Email or Password"
    )


@auth_router.get('/refresh_token')
async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer())):
    expiry_timestamp = token_details['exp']

    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
        new_access_token = create_access_token(
            user_data=token_details['user']
        )

        return JSONResponse(content={
            "access_token": new_access_token
        })

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")


@auth_router.get('/my_account')
async def get_account_credentials(user = Depends(get_current_user), _:bool= Depends(role_checker)):
    return user


@auth_router.get('/logout')
async def revoke_token(token_details: dict = Depends(AccessTokenBearer())):
    jti = token_details['jti']

    await add_jti_to_blocklist(jti)

    return JSONResponse(
        content={
            "message":"Logged out successfully"
        },
        status_code=status.HTTP_200_OK
    )

"""
1. Provide the email -> password reset request
2. Send password reset link
3. Reset password -> password reset confirmation
"""

@auth_router.post('/password-reset-request')
async def password_reset_request(email_data: PasswordResetRequestModel):
    email = email_data.email

    token = create_url_safe_token({"email":email})

    link = f"http://{settings.DOMAIN}/api/v1/auth/password-reset-confirm/{token}"

    html_message = f"""
    <h1>Reset your password</h1>
    <p>Please click this <a href="{link}">link</a> to reset your password</p>
    """
    emails=[email]
    subject="Reset your password"

    send_email.delay(emails, subject, html_message)

    return JSONResponse(
        content={"message":"Please check your email for instructions to reset your password"},
        status_code=status.HTTP_200_OK
    )


@auth_router.post('/password-reset-confirm/{token}')
async def reset_account_password(token: str, passwords: PasswordResetConfirmModel, session: AsyncSession = Depends(get_session)):
    new_password = passwords.new_password
    confirm_password = passwords.confirm_new_password
    
    if new_password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_308_PERMANENT_REDIRECT,
            detail="Passwords do not match"
        )

    token_data = decode_url_safe_token(token)

    user_email = token_data.get('email')

    if user_email:
        user = await user_service.get_user_by_email(user_email, session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message":"User with such email address not found"}
            )
        
        password_hash = generate_password_hash(new_password)
        await user_service.update_user(user, {'password_hash': password_hash}, session)

        return JSONResponse(content={
            "message":"Password reset successfully",
        }, status_code=status.HTTP_200_OK)
    
    return JSONResponse(
        content={"message":"Error occured during password reset"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )