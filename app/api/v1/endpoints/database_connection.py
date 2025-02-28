# from fastapi import APIRouter, HTTPException
# from app.models import DatabaseConnectionRequest
# from app.services.sql_agent import setup_database_connection
# from sqlalchemy.exc import OperationalError, DatabaseError
# from urllib.parse import urlparse

# router = APIRouter()

# @router.post("/setup-connection")
# async def setup_connection(request: DatabaseConnectionRequest):
#     try:
#         # Basic validation of connection string format
#         parsed = urlparse(request.connection_string)
#         if not all([parsed.scheme, parsed.netloc]):
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid connection string format. Expected format: dialect+driver://username:password@host:port/database"
#             )
            
#         setup_database_connection(request.connection_string)
#         return {"message": "Database connection established successfully!"}
#     except OperationalError as e:
#         raise HTTPException(
#             status_code=503,
#             detail=f"Failed to connect to database: Connection refused or invalid credentials. Details: {str(e)}"
#         )
#     except DatabaseError as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Database error occurred: {str(e)}"
#         )
#     except ValueError as e:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Invalid configuration: {str(e)}"
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Unexpected error occurred while setting up database connection: {str(e)}"
#         )

# app/api/v1/endpoints/database_connection.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.sql_agent_instance import sql_agent
from sqlalchemy.exc import OperationalError, DatabaseError
from urllib.parse import urlparse

router = APIRouter()

class DatabaseConnectionRequest(BaseModel):
    connection_string: str

@router.post("/setup-connection")
async def setup_connection(request: DatabaseConnectionRequest):
    try:
        # Basic validation of connection string format
        parsed = urlparse(request.connection_string)
        if not all([parsed.scheme, parsed.netloc]):
            raise HTTPException(
                status_code=400,
                detail="Invalid connection string format. Expected format: dialect+driver://username:password@host:port/database"
            )
            
        sql_agent.setup_database_connection(request.connection_string)
        return {"message": "Database connection established successfully!"}
    except OperationalError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to database: Connection refused or invalid credentials. Details: {str(e)}"
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error occurred: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid configuration: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error occurred while setting up database connection: {str(e)}"
        )