from pydantic import BaseModel, ConfigDict, SecretStr, field_validator
from datetime import datetime
from typing import Optional
import re

from src.models.users import UserRole

class UserValidations(BaseModel):
    username: str
    password: SecretStr
    
    @field_validator('username')
    def username_length(cls, v):
        if v is not None and (len(v) < 3 or len(v) > 50):
            raise ValueError("Username must be between 3 and 50 characters")
        return v
    
    @field_validator('password')
    def password_validation(cls, v):
        if v is not None:
            regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,50}$"
            if not re.search(regex, v.get_secret_value()):
                raise ValueError("Password must be between 8 and 50 characters and contain at least one uppercase letter, one lowercase letter, one integer, and one special character.")
        return v
    
class CreateUser(UserValidations):
    available : bool = True
     
class UpdateUser(UserValidations):
    username: str | None = None
    available: bool | None = None
    password: SecretStr | None = None
    role: UserRole | None = None
    
class ReadUser(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    id: int
    username: str
    available: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
class ReadAllUsers(BaseModel):
    id : int
    username : str
    available : bool
        
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
    
class RefreshTokenRequest(BaseModel):
    refresh_token: str