from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import sql_query, database_connection
from app.api.v1 import auth

app = FastAPI()

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],  # Allow all origin
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow al
)

app.include_router(database_connection.router, prefix="/api/v1")
app.include_router(sql_query.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1/auth")