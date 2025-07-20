
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
import sqlite3
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DB_PATH = "users.db"  # Adjust path if needed

def get_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int | None = None
    username: str

def get_user_by_username(conn, username: str):
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cur.fetchone()
    except Exception as e:
        return None

def create_user(conn, username: str, password: str):
    try:
        hashed_password = pwd_context.hash(password)
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    except Exception as e:
        return None

@router.post("/signup", response_model=UserOut)
def signup(user: UserCreate):
    try:
        conn = get_db()
        if get_user_by_username(conn, user.username):
            raise HTTPException(status_code=400, detail="Username already exists")
        user_id = create_user(conn, user.username, user.password)
        if not user_id:
            raise HTTPException(status_code=400, detail="Could not create user")
        return {"id": user_id, "username": user.username}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signup error: {str(e)}")

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        conn = get_db()
        user = get_user_by_username(conn, form_data.username)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        try:
            valid = pwd_context.verify(form_data.password, user["password"])
        except Exception:
            raise HTTPException(status_code=500, detail="Password verification error")
        if not valid:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        # Defensive: handle missing id column
        user_id = user["id"] if "id" in user.keys() else None
        return {"id": user_id, "username": user["username"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")
