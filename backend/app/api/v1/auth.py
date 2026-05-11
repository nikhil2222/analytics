from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserResponse
from app.db.session import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.schemas.invite import InviteRequest, InviteAcceptRequest
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole

router = APIRouter(prefix="/auth", tags=["Auth"])

REFRESH_COOKIE = "refresh_token"


def set_refresh_cookie(response: Response, token: str):
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=False,      # True in production
        samesite="lax",
        max_age=7 * 24 * 3600,
    )


@router.post("/register", response_model=TokenResponse)
async def register(data: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user, access_token, refresh_token = await AuthService(db).register(data)
    set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user, access_token, refresh_token = await AuthService(db).login(data)
    set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    access_token = await AuthService(db).refresh(token)
    return TokenResponse(access_token=access_token)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(REFRESH_COOKIE)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/invite")
async def invite_user(
    data: InviteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
):
    invite = await AuthService(db).invite_user(data, current_user)
    return {"message": "Invite created", "invite_token": invite.token}


@router.post("/invite/accept", response_model=TokenResponse)
async def accept_invite(data: InviteAcceptRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user, access_token, refresh_token = await AuthService(db).accept_invite(data)
    set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)