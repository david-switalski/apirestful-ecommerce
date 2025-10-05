from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.status import HTTP_404_NOT_FOUND, HTTP_409_CONFLICT, HTTP_400_BAD_REQUEST

from src.core.config import settings
from src.core.exceptions import (
    LastAdminError, UselessOperationError, UsernameAlreadyExistsError, UserHasOrdersError,
    ProductNameAlreadyExistsError, ProductInUseError, ProductUnavailableError,
    ProductNotFound, InsufficientStock, EmptyOrder
)
from fastapi.middleware.cors import CORSMiddleware
from src.routers.products import router as products_router
from src.routers.users import router as users_router
from src.routers.orders import router as orders_router

# Create FastAPI application instance with project metadata
app = FastAPI(
    title = settings.PROJECT_NAME, 
    version = settings.PROJECT_VERSION
)

# Include routers for products, users and orders endpoints
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(users_router)

# MIDDLEWARE & ROUTERS
@app.exception_handler(ProductNotFound)
async def product_not_found_exception_handler(request: Request, exc: ProductNotFound):
    return JSONResponse(status_code=HTTP_404_NOT_FOUND, content={"detail": str(exc)})

@app.exception_handler(UselessOperationError)
@app.exception_handler(EmptyOrder)
async def bad_request_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=HTTP_400_BAD_REQUEST, content={"detail": str(exc)})

@app.exception_handler(UsernameAlreadyExistsError)
@app.exception_handler(ProductNameAlreadyExistsError)
@app.exception_handler(ProductInUseError)
@app.exception_handler(LastAdminError)
@app.exception_handler(InsufficientStock)
@app.exception_handler(UserHasOrdersError)
@app.exception_handler(ProductUnavailableError)
async def conflict_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=HTTP_409_CONFLICT, content={"detail": str(exc)})

# List of allowed origins for CORS
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

# Add CORS middleware to allow cross-origin requests from specified origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    """
    Root endpoint that returns a welcome message and documentation hint.
    """
    return {"message": "¡Welcome to my API! Visit /docs for the documentation."}