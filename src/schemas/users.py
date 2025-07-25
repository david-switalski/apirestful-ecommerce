from pydantic import BaseModel, ConfigDict
import datetime

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
    model_config = ConfigDict(from_attributes=True)
    id : int
    created_at : datetime
    updated_at : datetime
    
    

    