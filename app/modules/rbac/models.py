from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Table, Column, Integer
from app.database import Base

# Role va Permission o'rtasidagi many-to-many bog'liqlik jadvali
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

# User va Role o'rtasidagi many-to-many bog'liqlik jadvali
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

class Permission(Base):
    __tablename__ = "permissions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False) # Masalan: "user:create"
    description: Mapped[str] = mapped_column(String(200), nullable=True)

    def __repr__(self):
        return f"<Permission(name='{self.name}')>"

class Role(Base):
    __tablename__ = "roles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False) # Masalan: "admin", "hr"
    description: Mapped[str] = mapped_column(String(200), nullable=True)

    # Bog'liqliklar
    permissions = relationship("Permission", secondary=role_permissions, backref="roles", lazy="selectin")

    def __repr__(self):
        return f"<Role(name='{self.name}')>"
