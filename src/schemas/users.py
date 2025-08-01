from pydantic import BaseModel, ConfigDict, SecretStr, field_validator
from datetime import datetime
from typing import Optional
import regex as re

class User(BaseModel):
    username : str
    available : bool = True
    
class CreateUser(User):
    password : SecretStr
    
    @field_validator('username')
    def username_length(cls, v):
        if len(v) < 3 or len(v) > 50:
            raise ValueError("Username must be between 3 and 50 characters")
        return v
    
    @field_validator('password')
    def password_validation(cls, v):
        regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,50}$"
        
        if not re.search(regex, v.get_secret_value()):
            raise ValueError("The password must be between 8 and 50 characters and must contain at least one uppercase letter, one lowercase letter, one integer and one character.")
        return v
     
class UpdateUser(BaseModel):
    username : str | None = None
    available : bool | None = None
    password : SecretStr | None = None
    
class ReadUser(User):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    id : int
    
    created_at : Optional[datetime]
    updated_at: Optional[datetime]
    
    
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
    