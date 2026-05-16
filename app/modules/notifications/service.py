from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.modules.notifications.models import Notification, UserDevice, NotificationType
from app.modules.notifications.schemas import NotificationCreate, DeviceTokenCreate
from app.modules.users.models import User, UserRole
from app.modules.notifications.ws_manager import manager
from typing import List

class NotificationService:
    @staticmethod
    async def create_notification(db: AsyncSession, data: NotificationCreate):
        """Bildirishnoma yaratish va real vaqtda yuborish"""
        users_to_notify = []
        target_name = ""
        
        if data.to_all:
            # Barcha aktiv foydalanuvchilar
            stmt = select(User.id).where(User.is_active == True)
            res = await db.execute(stmt)
            users_to_notify = res.scalars().all()
            target_name = "Barcha foydalanuvchilarga"
        elif data.role:
            # Ma'lum roldagi foydalanuvchilar
            stmt = select(User.id).where(User.role == data.role, User.is_active == True)
            res = await db.execute(stmt)
            users_to_notify = res.scalars().all()
            target_name = f"Barcha {data.role.value} xodimlariga"
        elif data.user_id:
            # Bitta foydalanuvchi
            user = await db.get(User, data.user_id)
            if user:
                users_to_notify = [user.id]
                target_name = f"{user.first_name}ga"
            else:
                users_to_notify = []
                target_name = "Noma'lum foydalanuvchiga"

        notifications = []
        for u_id in users_to_notify:
            new_notif = Notification(
                user_id=u_id,
                title=data.title,
                message=data.message,
                type=data.type
            )
            db.add(new_notif)
            notifications.append(new_notif)
            
            # Real-time yuborish
            await manager.send_personal_message({
                "type": "notification",
                "title": data.title,
                "message": data.message,
                "notif_type": data.type.value
            }, u_id)

        await db.commit()
        return len(notifications), target_name

    @staticmethod
    async def send_internal_notification(db: AsyncSession, user_id: int, title: str, message: str, n_type: NotificationType = NotificationType.INFO):
        """Ichki xizmatlar (Attendance, Salary, etc.) orqali bildirishnoma yuborish"""
        new_notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=n_type
        )
        db.add(new_notif)
        
        # Real-time yuborish
        await manager.send_personal_message({
            "type": "notification",
            "title": title,
            "message": message,
            "notif_type": n_type.value
        }, user_id)
        
        # Mock push yuborish
        await NotificationService.send_push_mock(user_id, title, message)
        
        await db.commit()
        return True

    @staticmethod
    async def get_my_notifications(db: AsyncSession, user_id: int, only_unread: bool = False):
        stmt = select(Notification).where(Notification.user_id == user_id)
        if only_unread:
            stmt = stmt.where(Notification.is_read == False)
        stmt = stmt.order_by(Notification.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def mark_as_read(db: AsyncSession, user_id: int, notif_id: int = None):
        stmt = update(Notification).where(Notification.user_id == user_id)
        if notif_id:
            stmt = stmt.where(Notification.id == notif_id)
        stmt = stmt.values(is_read=True)
        await db.execute(stmt)
        await db.commit()
        return True

    @staticmethod
    async def save_device_token(db: AsyncSession, user_id: int, data: DeviceTokenCreate):
        # Eski tokenni tekshirish
        stmt = select(UserDevice).where(UserDevice.fcm_token == data.fcm_token)
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        
        if existing:
            existing.user_id = user_id
            existing.device_type = data.device_type
        else:
            new_device = UserDevice(
                user_id=user_id,
                fcm_token=data.fcm_token,
                device_type=data.device_type
            )
            db.add(new_device)
        
        await db.commit()
        return True

    @staticmethod
    async def send_push_mock(user_id: int, title: str, message: str):
        """Push bildirishnoma yuborish uchun mock (Firebase o'rniga)"""
        print(f"PUSH SENT to User {user_id}: {title} - {message}")
        return True
