from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import sqlite3
import os

from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()



base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "Student.db")

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
def login(user: User):

    cursor.execute(
        "SELECT * FROM Users WHERE username=?",
        (user.username,)
    )

    data = cursor.fetchone()

    if not data:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    stored_password = data[2]

    password_correct = pwd_context.verify(
        user.password,
        stored_password
    )

    if not password_correct:
        raise HTTPException(
            status_code=401,
            detail="Invalid password"
        )

    # Dummy Token
    token = user.username + "_token"

    return {
        "access_token": token,
        "token_type": "bearer"
    }



def verify_token(
    token: str = Depends(oauth2_scheme)
):

    if "_token" not in token:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    return token



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
    token: str = Depends(verify_token)
):

    cursor.execute(
        "INSERT INTO Students VALUES (?,?,?)",
        (student.id, student.name, student.marks)
    )

    conn.commit()

    return {
        "message": "Student added successfully"
    }



@app.put("/students/{id}")
def update_student(
    id: int,
    student: Student,
    token: str = Depends(verify_token)
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
        "message": "Updated successfully"
    }



@app.delete("/students/{id}")
def delete_student(
    id: int,
    token: str = Depends(verify_token)
):

    cursor.execute(
        "DELETE FROM Students WHERE id=?",
        (id,)
    )

    conn.commit()

    return {
        "message": "Deleted successfully"
    }
