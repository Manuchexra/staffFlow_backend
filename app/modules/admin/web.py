from fastapi import APIRouter, Depends, Request, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.modules.users.models import User, UserRole
from app.modules.users.service import UserService
from app.modules.rbac.service import RBACService
from app.modules.reports.service import ReportService
from app.core.security import verify_password, create_access_token, decode_token

router = APIRouter(prefix="/admin", tags=["Admin Panel"])
templates = Jinja2Templates(directory="templates")

async def get_admin_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user = await db.get(User, int(user_id))
    if not user or user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return user

@router.get("/", response_class=HTMLResponse)
async def admin_root(request: Request):
    return RedirectResponse(url="/admin/dashboard")

@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request, error: str = ""):
    return templates.TemplateResponse("admin/login.html", {"request": request, "error": error})

@router.post("/login", response_class=HTMLResponse)
async def admin_login(
    request: Request,
    identifier: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where((User.phone == identifier) | (User.email == identifier))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or user.role != UserRole.ADMIN or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "error": "Aniq ma'lumotlar noto'g'ri yoki siz admin emassiz."},
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    token = create_access_token(str(user.id))
    response = RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=3600,
        samesite="lax",
    )
    return response

@router.post("/logout")
async def admin_logout():
    response = RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, current_user: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    summary = await ReportService.get_dashboard_summary(db)
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "current_user": current_user, "summary": summary}
    )

@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    search: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    role_enum = None
    if role:
        try:
            role_enum = UserRole[role]
        except KeyError:
            try:
                role_enum = UserRole(role)
            except ValueError:
                role_enum = None

    users = await UserService.get_all_users(db, search=search, role=role_enum, is_active=is_active)
    return templates.TemplateResponse(
        "admin/users.html",
        {"request": request, "current_user": current_user, "users": users, "search": search, "role": role, "is_active": is_active}
    )

@router.get("/roles", response_class=HTMLResponse)
async def admin_roles(request: Request, current_user: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    roles = await RBACService.get_all_roles(db)
    return templates.TemplateResponse(
        "admin/roles.html",
        {"request": request, "current_user": current_user, "roles": roles}
    )

@router.get("/permissions", response_class=HTMLResponse)
async def admin_permissions(request: Request, current_user: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    permissions = await RBACService.get_all_permissions(db)
    return templates.TemplateResponse(
        "admin/permissions.html",
        {"request": request, "current_user": current_user, "permissions": permissions}
    )
