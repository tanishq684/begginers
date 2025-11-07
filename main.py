from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Integer, Float, Text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Optional, List, Dict, Any
import random

DATABASE_URL = "sqlite:///./study_resources.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

app = FastAPI(title="Personalized Study Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to frontend host in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    weightage = Column(Float)  # percent (10.0 means 10%)

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

@app.get("/study_materials", response_model=Dict[str, List[Dict[str, Any]]])
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
    return grouped

@app.get("/subject_weightage", response_model=List[Dict[str, Any]])
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
    return results

def generate_quiz_for_topic(topic: str) -> Dict[str, Any]:
    options = ["A", "B", "C", "D"]
    return {
        "question": f"Sample question on {topic}",
        "options": options,
        "answer": random.choice(options)
    }

@app.post("/ai_assistant/plan", response_model=Dict[str, Any])
def ai_assistant_plan(
    weak_topics: List[str] = Query(..., description="List of topics to focus on"),
    grade: Optional[str] = Query(None),
    exam: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    if not weak_topics:
        raise HTTPException(status_code=400, detail="You must provide at least one weak topic.")
    materials_query = db.query(Resource)
    if grade: materials_query = materials_query.filter(Resource.grade == grade)
    if exam: materials_query = materials_query.filter(Resource.exam.ilike(exam))
    if subject: materials_query = materials_query.filter(Resource.subject.ilike(subject))
    recommended_resources = []
    for t in weak_topics:
        topic_resources = materials_query.filter(Resource.topic==t).all()
        for r in topic_resources:
            recommended_resources.append({
                "topic": t,
                "type": r.type,
                "url": r.url,
                "description": r.description,
            })
    plan = [{"day": i+1, "topic": t, "recommended_action": f"Study {t}", "recommended_materials": [
        res for res in recommended_resources if res["topic"] == t
    ]} for i, t in enumerate(weak_topics)]
    quiz = [generate_quiz_for_topic(t) for t in weak_topics]
    return {"plan": plan, "quiz": quiz}

# If you need full OpenAPI docs, run with `uvicorn main:app --reload`