from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import sqlite3
import os

from passlib.context import CryptContext

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from jose import jwt
from datetime import datetime, timedelta

from dotenv import load_dotenv


load_dotenv()

app = FastAPI()


SECRET_KEY = os.getenv("SECRET_KEY")

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 30


base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, Student.db)

conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS Students(
    id INTEGER PRIMARY KEY,
    name TEXT,
    marks INTEGER
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS Users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

conn.commit()



pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login"
)



def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update(
        {"exp": expire}
    )

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt



class Student(BaseModel):
    id: int
    name: str
    marks: int


class User(BaseModel):
    username: str
    password: str



@app.post("/signup")
def signup(user: User):

    cursor.execute(
        "SELECT * FROM Users WHERE username=?",
        (user.username,)
    )

    existing_user = cursor.fetchone()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    hashed_password = pwd_context.hash(
        user.password
    )

    cursor.execute(
        "INSERT INTO Users(username,password) VALUES (?,?)",
        (user.username, hashed_password)
    )

    conn.commit()

    return {
        "message": "User created successfully"
    }


@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends()
):

    cursor.execute(
        "SELECT * FROM Users WHERE username=?",
        (form_data.username,)
    )

    data = cursor.fetchone()

    if not data:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    stored_password = data[2]

    password_correct = pwd_context.verify(
        form_data.password,
        stored_password
    )

    if not password_correct:
        raise HTTPException(
            status_code=401,
            detail="Invalid password"
        )

    access_token = create_access_token(
        data={"sub": form_data.username}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


def verify_token(
    token: str = Depends(oauth2_scheme)
):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")

        if username is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        return username

    except:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )



@app.get("/students")
def get_students():

    cursor.execute(
        "SELECT * FROM Students"
    )

    data = cursor.fetchall()

    return data



@app.get("/students/{id}")
def get_student(id: int):

    cursor.execute(
        "SELECT * FROM Students WHERE id=?",
        (id,)
    )

    data = cursor.fetchone()

    if not data:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return data



@app.post("/students")
def add_student(
    student: Student,
    current_user: str = Depends(verify_token)
):

    cursor.execute(
        "INSERT INTO Students VALUES (?,?,?)",
        (student.id, student.name, student.marks)
    )

    conn.commit()

    return {
        "message": f"Student added by {current_user}"
    }



@app.put("/students/{id}")
def update_student(
    id: int,
    student: Student,
    current_user: str = Depends(verify_token)
):

    cursor.execute(
        """
        UPDATE Students
        SET name=?, marks=?
        WHERE id=?
        """,
        (student.name, student.marks, id)
    )

    conn.commit()

    return {
        "message": f"Updated by {current_user}"
    }



@app.delete("/students/{id}")
def delete_student(
    id: int,
    current_user: str = Depends(verify_token)
):

    cursor.execute(
        "DELETE FROM Students WHERE id=?",
        (id,)
    )

    conn.commit()

    return {
        "message": f"Deleted by {current_user}"
    }
