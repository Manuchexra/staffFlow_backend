from pydantic import BaseModel, Field
from typing import List, Optional

class PermissionBase(BaseModel):
    name: str = Field(..., example="user:read")
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class PermissionResponse(PermissionBase):
    id: int
    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    name: str = Field(..., example="hr_manager")
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class RoleResponse(RoleBase):
    id: int
    permissions: List[PermissionResponse] = []
    class Config:
        from_attributes = True

class AssignPermissions(BaseModel):
    permission_ids: List[int]

class AssignRoles(BaseModel):
    role_ids: List[int]
