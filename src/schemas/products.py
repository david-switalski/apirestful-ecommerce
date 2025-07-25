from pydantic import BaseModel, ConfigDict, Dateti
import datetime

class Product(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name : str
    category : str
    price : float
    stock : int
    description : str
    available : bool = True
    
class CreateProduct(Product):
    pass
    
class UpdateProduct(BaseModel):
    name : str | None = None
    category : str | None = None 
    price : float | None = None
    stock : int | None = None
    description : str | None = None
    available : bool | None = None
    
class ReadProduct(Product):
    model_config = ConfigDict(from_attributes=True)
    id : int 
    
    created_at : datetime
    updated_at : datetime
    
                                         
                                         
                                         