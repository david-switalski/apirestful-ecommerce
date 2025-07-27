from fastapi import FastAPI
from src.core.config import settings
from src.data_base import base
from src.routers.products import router as products_router
from src.routers.users import router as users_router

app = FastAPI(
    title = settings.PROJECT_NAME, 
    version = settings.PROJECT_VERSION
)

app.include_router(products_router)
app.include_router(users_router)

@app.get("/")
async def read_root():
    return {"message": "¡Bienvenido a mi API! Visita /docs para la documentación."}
    
