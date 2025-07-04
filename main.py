from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated
import models
from database import SessionLocal, engine
from sqlalchemy.orm import Session

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

class ChoiceBase(BaseModel):
    choice_text: str
    is_correct: bool = False

class QuestionBase(BaseModel):
    question_text: str
    choices: List[ChoiceBase]
    

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        

db_dependency = Annotated[Session, Depends(get_db)]


@app.get("/questions/{question_id}", response_model=QuestionBase)
async def read_question(question_id: int, db: db_dependency):
    result = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Question not found")

    choices = db.query(models.Choices).filter(models.Choices.question_id == question_id).all()
    return QuestionBase(
        question_text=result.question_text,
        choices=[ChoiceBase(choice_text=choice.choice_text, is_correct=choice.is_correct) for choice in choices]
    )

@app.get("/choices/{question_id}", response_model=List[ChoiceBase])
async def read_choices(question_id: int, db: db_dependency):
    choices = db.query(models.Choices).filter(models.Choices.question_id == question_id).all()
    if not choices:
        raise HTTPException(status_code=404, detail="Choice not found")
    return [ChoiceBase(choice_text=choice.choice_text, is_correct=choice.is_correct) for choice in choices]

@app.post("/questions/", response_model=None)
async def create_question(question: QuestionBase, db: db_dependency):
    db_question = models.Question(question_text=question.question_text)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)

    for choice in question.choices:
        db_choice = models.Choices(
            choice_text=choice.choice_text,
            is_correct=choice.is_correct,
            question_id=db_question.id
        )
        db.add(db_choice)

    db.commit()
    