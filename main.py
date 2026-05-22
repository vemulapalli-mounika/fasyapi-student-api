from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import os
app=FastAPI()
base_dir=os.path.dirname(os.path.abspath(__file__))
db_path=os.path.join(base_dir,"Student.db")

conn=sqlite3.connect(db_path,check_same_thread=False)
cursor=conn.cursor()
cursor.execute("""
CREATE TABLE  IF NOT EXISTS Students(
               id INTEGER PRIMARY KEY,
               name TEXT,
               marks INTEGER
               )
               """)
conn.commit()

class Student(BaseModel):
    id:int
    name:str
    marks:int

@app.get("/students")
def get_students():
    cursor.execute("select * from Students")
    data=cursor.fetchall()
    conn.commit()
    return data
@app.get("/students/{id}")
def get_student(id:int):
    cursor.execute("select * from Students where id=?",
                   (id,))
    data=cursor.fetchone()
    return data
@app.post("/students")
def add_student(student:Student):
    cursor.execute(
        "Insert into Students values (?,?,?)",
        (student.id,student.name,student.marks)
    )
    conn.commit()
    return {"Message":"student added successfully"}
@app.put("/students/{id}")
def update_student(id:int,student:Student):
    cursor.execute(
        """ 
        update Students
        set name=?,marks=?
        where id=?
        """,
        (student.name,student.marks,id))
    conn.commit()
    return {"message":"updated successfully"}
@app.delete("/students/{id}")
def delete_student(id:int):
    cursor.execute(
        "delete from Students where id=?",
        (id,)
    )
    conn.commit()
    return {"message":"deleted successfully"}
