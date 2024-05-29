from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import List

# MongoDB connection
MONGO_DETAILS = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_DETAILS)
database = client.local
students_collection = database.get_collection("StudentData")

class StudentModel(BaseModel):
    name: str
    email: EmailStr
    age: int = Field(..., ge=18, le=100)
    gpa: float = Field(..., ge=0.0, le=4.0)

class StudentDB(StudentModel):
    id: str

def student_helper(student) -> StudentDB:
    return StudentDB(
        id=str(student["_id"]),
        name=student["name"],
        email=student["email"],
        age=student["age"],
        gpa=student["gpa"],
    )

app = FastAPI()

@app.post("/students/", response_model=StudentDB)
async def create_student(student: StudentModel):
    student_dict = student.dict()
    result = await students_collection.insert_one(student_dict)
    student_dict["_id"] = result.inserted_id
    return student_helper(student_dict)

@app.get("/students/", response_model=List[StudentDB])
async def get_students():
    students = []
    async for student in students_collection.find():
        students.append(student_helper(student))
    return students

@app.get("/students/{student_id}", response_model=StudentDB)
async def get_student(student_id: str):
    student = await students_collection.find_one({"_id": ObjectId(student_id)})
    if student:
        return student_helper(student)
    raise HTTPException(status_code=404, detail="Student not found")


@app.delete("/students/{student_id}")
async def delete_student(student_id: str):
    delete_result = await students_collection.delete_one({"_id": ObjectId(student_id)})
    if delete_result.deleted_count == 1:
        return {"message": "Student deleted successfully"}
    raise HTTPException(status_code=404, detail="Student not found")
