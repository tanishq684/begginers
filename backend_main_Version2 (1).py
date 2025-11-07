from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional

app = FastAPI()

class Resource(BaseModel):
    id: str
    type: str  # "YouTube", "PDF", "QuestionPaper"
    topic: str
    difficulty: str  # "Easy", "Medium", "Hard"
    subject: str
    url: str
    solutions_url: Optional[str] = None
    description: Optional[str] = None  # NEW: Add for descriptive topics!

# Example in-memory data
resources = [
    Resource(
        id="yt1", 
        type="YouTube", 
        topic="Algebra", 
        difficulty="Easy", 
        subject="Math", 
        url="https://youtube.com/abc123",
        description="An overview of algebraic foundations, including variables and equations."
    ),
    Resource(
        id="pdf1", 
        type="PDF", 
        topic="Algebra", 
        difficulty="Easy", 
        subject="Math", 
        url="/pdfs/algebra1.pdf"
    ),
    Resource(
        id="qp1", 
        type="QuestionPaper", 
        topic="Algebra", 
        difficulty="Medium", 
        subject="Math", 
        url="/qp/algebra2022.pdf", 
        solutions_url="/qp/algebra2022-sol.pdf"
    ),
    Resource(
        id="yt2", 
        type="YouTube", 
        topic="Geometry", 
        difficulty="Hard", 
        subject="Math", 
        url="https://youtube.com/def456",
        description="Advanced geometry concepts, covering theorems, proofs, and real-world applications."
    ),
]

@app.get("/aggregate_resources")
def aggregate_resources():
    grouped: Dict[str, Dict[str, List[Resource]]] = {}
    for resource in resources:
        grouped.setdefault(resource.topic, {}).setdefault(resource.difficulty, []).append(resource)
    # Convert objects to dict for JSON
    res = {t: {d: [r.dict() for r in grouped[t][d]] for d in grouped[t]} for t in grouped}
    return {"grouped": res}