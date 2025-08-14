from fastapi import FastAPI
from src.core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from src.routers.products import router as products_router
from src.routers.users import router as users_router
from fastapi.responses import JSONResponse
from fastapi import Request
from src.core.exceptions import LastAdminError, UselessOperationError

app = FastAPI(
    title = settings.PROJECT_NAME, 
    version = settings.PROJECT_VERSION
)

app.include_router(products_router)
app.include_router(users_router)


origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"message": "¡Welcome to my API! Visit /docs for the documentation."}
    
    
@app.exception_handler(LastAdminError)
async def last_admin_exception_handler(request: Request, exc: LastAdminError):
    return JSONResponse(
        status_code=400,
        content={"detail": str (exc)}
    )
    
@app.exception_handler(UselessOperationError)
async def useless_operation_exception_handler(request: Request, exc: UselessOperationError):
    return JSONResponse(
        status_code=400,
        content={"detail": str (exc)},
    )