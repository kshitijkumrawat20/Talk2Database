from pydantic import BaseModel, validator
from urllib.parse import urlparse
import re

class DatabaseConnectionRequest(BaseModel):
    connection_string: str  # e.g., "mysql+pymysql://user:password@host:port/database"

    @validator('connection_string')
    def validate_connection_string(cls, v):
        if not v:
            raise ValueError("Connection string cannot be empty")
        
        # Check if string follows basic URL format
        try:
            # Basic format check
            if not re.match(r'^[a-zA-Z]+(\+[a-zA-Z]+)?://[^/]+/.+$', v):
                raise ValueError("Invalid connection string format - must follow pattern: dialect+driver://username:password@host:port/database")
            
            # Parse URL to validate components
            parsed = urlparse(v)
            
            # Validate scheme (database type)
            if not parsed.scheme:
                raise ValueError("Database type must be specified")
            
            # Validate that we have a hostname
            if not parsed.hostname:
                raise ValueError("Host must be specified")
            
            # Validate that we have a database name
            if not parsed.path or parsed.path == '/':
                raise ValueError("Database name must be specified")
            
            # Validate port if present
            if parsed.port and (parsed.port < 1 or parsed.port > 65535):
                raise ValueError("Port number must be between 1 and 65535")

            return v
        except Exception as e:
            raise ValueError(f"Invalid connection string: {str(e)}")
    # Alternatively, you can break it down into individual fields:
    # db_type: str  # e.g., "mysql", "postgres"
    # host: str
    # port: int
    # database: str
    # username: str
    # password: str
class SQLQueryRequest(BaseModel):
    query: str

class SQLQueryResponse(BaseModel):
    result: str
