import pydantic
from typing import Optional
import uuid


class User(pydantic.BaseModel):
    id: str = pydantic.Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    age: int
    email: str
    password: str
    role: str  # student, teacher, admin
    
    @pydantic.validator('role')
    def validate_role(cls, v):
        valid_roles = ['student', 'teacher', 'admin']
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {valid_roles}')
        return v
    
    @pydantic.validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v
    
    @pydantic.validator('age')
    def validate_age(cls, v):
        if v < 0 or v > 120:
            raise ValueError('Age must be between 0 and 120')
        return v

