from fastapi import FastAPI, Depends, Query
from sqlalchemy import create_engine, Column, String, Integer, Float, Text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Optional, List, Dict
import random

DATABASE_URL = "sqlite:///./study_resources.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

app = FastAPI()

class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True)  # "YouTube", "PDF", "QuestionPaper"
    grade = Column(String, index=True)
    exam = Column(String, index=True)  # School, JEE, NEET, etc.
    subject = Column(String, index=True)
    topic = Column(String, index=True)
    difficulty = Column(String, index=True)
    url = Column(String)
    solutions_url = Column(String, nullable=True)
    description = Column(Text, nullable=True)

class SubjectWeightage(Base):
    __tablename__ = "subject_weightages"
    id = Column(Integer, primary_key=True, index=True)
    grade = Column(String, index=True)
    exam = Column(String, index=True)
    subject = Column(String, index=True)
    topic = Column(String, index=True)
    weightage = Column(Float)  # e.g. percent (10.0 means 10%)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def seed_data():
    db = SessionLocal()
    if db.query(Resource).count() == 0:
        data = [
            Resource(type="YouTube", grade="10", exam="School", subject="Math", topic="Algebra", difficulty="Easy",
                     url="https://youtube.com/algebra_intro", description="Basics of algebra for class 10."),
            Resource(type="PDF", grade="10", exam="School", subject="Math", topic="Algebra", difficulty="Easy",
                     url="/pdfs/algebra10.pdf", description="Class 10 algebra notes."),
            Resource(type="QuestionPaper", grade="10", exam="School", subject="Math", topic="Algebra", difficulty="Medium",
                     url="/qp/class10-math-2022.pdf", solutions_url="/qp/class10-math-2022-sol.pdf", description="Previous year paper for class 10 math."),
            Resource(type="YouTube", grade="10", exam="JEE", subject="Physics", topic="Mechanics", difficulty="Medium",
                     url="https://youtube.com/jee_mechanics", description="Mechanics concepts for JEE Physics."),
            Resource(type="QuestionPaper", grade="10", exam="JEE", subject="Physics", topic="Mechanics", difficulty="Hard",
                     url="/qp/jee-physics-2023.pdf", solutions_url="/qp/jee-physics-2023-sol.pdf", description="JEE previous year Physics Mechanics."),
        ]
        db.bulk_save_objects(data)
        db.commit()
    if db.query(SubjectWeightage).count() == 0:
        weights = [
            SubjectWeightage(grade="10", exam="School", subject="Math", topic="Algebra", weightage=25.0),
            SubjectWeightage(grade="10", exam="School", subject="Math", topic="Geometry", weightage=20.0),
            SubjectWeightage(grade="10", exam="JEE", subject="Physics", topic="Mechanics", weightage=35.0),
        ]
        db.bulk_save_objects(weights)
        db.commit()
    db.close()

seed_data()

@app.get("/study_materials")
def study_materials(
    grade: Optional[str] = Query(None),
    exam: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Resource)
    if grade: query = query.filter(Resource.grade == grade)
    if exam: query = query.filter(Resource.exam.ilike(exam))
    if subject: query = query.filter(Resource.subject.ilike(subject))
    resources = query.all()
    grouped: Dict[str, List[Dict]] = {}
    for r in resources:
        grouped.setdefault(r.topic, []).append({
            "id": r.id,
            "type": r.type,
            "grade": r.grade,
            "exam": r.exam,
            "subject": r.subject,
            "topic": r.topic,
            "difficulty": r.difficulty,
            "url": r.url,
            "solutions_url": r.solutions_url,
            "description": r.description,
        })
    return {"materials": grouped}

@app.get("/subject_weightage")
def subject_weightage(
    grade: Optional[str] = Query(None),
    exam: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(SubjectWeightage)
    if grade: query = query.filter(SubjectWeightage.grade == grade)
    if exam: query = query.filter(SubjectWeightage.exam.ilike(exam))
    if subject: query = query.filter(SubjectWeightage.subject.ilike(subject))
    weightages = query.all()
    results = [{
        "grade": w.grade,
        "exam": w.exam,
        "subject": w.subject,
        "topic": w.topic,
        "weightage": w.weightage,
    } for w in weightages]
    return {"weightages": results}

# AI assistant endpoint (stubbed)
@app.post("/ai_assistant/plan")
def ai_assistant_plan(weak_topics: List[str] = Query(...)):
    # Stub logic: recommend topics and simulate quiz generation (replace with real OpenAI or ML logic)
    plan = [{"day": i+1, "topic": t, "recommended_action": f"Study {t}"} for i, t in enumerate(weak_topics)]
    quiz = [{"question": f"Sample question on {t}", "options": ["A", "B", "C"], "answer": random.choice(["A", "B", "C"])} for t in weak_topics]
    return {"plan": plan, "quiz": quiz}