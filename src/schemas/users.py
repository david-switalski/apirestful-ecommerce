from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class User(BaseModel):
    username : str
    available : bool = True
    
class CreateUser(User):
    password : str
     
class UpdateUser(BaseModel):
    username : str | None = None
    available : bool | None = None
    password : str | None = None
    
class ReadUser(User):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    id : int
    
    created_at : Optional[datetime]
    updated_at: Optional[datetime]
    
    

    