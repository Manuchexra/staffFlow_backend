from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_current_user, require_role, UserRole, decode_token, is_token_blacklisted
from app.modules.users.models import User
from app.modules.notifications.schemas import NotificationCreate, NotificationResponse, DeviceTokenCreate
from app.modules.notifications.service import NotificationService
from app.modules.notifications.ws_manager import manager
from typing import List

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/", response_model=List[NotificationResponse], summary="[Auth] Bildirishnomalar tarixini ko'rish")
async def list_my_notifications(
    only_unread: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await NotificationService.get_my_notifications(db, current_user.id, only_unread)

@router.post("/read/{notif_id}", summary="[Auth] Bildirishnomani o'qilgan deb belgilash")
async def mark_read(
    notif_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await NotificationService.mark_as_read(db, current_user.id, notif_id)
    return {"message": "O'qilgan deb belgilandi"}

@router.post("/read-all", summary="[Auth] Barcha bildirishnomalarni o'qilgan deb belgilash")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await NotificationService.mark_as_read(db, current_user.id)
    return {"message": "Hammasi o'qilgan deb belgilandi"}

@router.post("/send", summary="[Admin/HR] Bildirishnoma yuborish")
async def send_notification(
    data: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.HR_MANAGER))
):
    """
    Individual, rol bo'yicha yoki barcha foydalanuvchilarga xabar yuborish.
    """
    count = await NotificationService.create_notification(db, data)
    return {"message": f"{count} ta foydalanuvchiga yuborildi"}

@router.post("/device-token", summary="[Auth] Push token saqlash")
async def save_token(
    data: DeviceTokenCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await NotificationService.save_device_token(db, current_user.id, data)
    return {"message": "Token saqlandi"}

# --- WebSocket ---

@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str, db: AsyncSession = Depends(get_db)):
    """
    Real-time bildirishnomalar uchun WebSocket ulanishi.
    Token orqali autentifikatsiya qilinadi.
    """
    payload = decode_token(token)
    if not payload or await is_token_blacklisted(token):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    user_id = int(payload.get("sub"))
    await manager.connect(user_id, websocket)
    try:
        while True:
            # Kutish rejimi (keep-alive uchun)
            data = await websocket.receive_text()
            # Xabarlarni qabul qilish shart emas, lekin ulanishni ushlab turish uchun kerak
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
