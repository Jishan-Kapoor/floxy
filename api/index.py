from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Answer(BaseModel):
    question_id: int
    answer: str

class QuizSubmission(BaseModel):
    answers: List[Answer]

QUIZ_QUESTIONS = [
    {
        "id": 1,
        "question": "Who is called the Father of Genetics?",
        "options": ["Gregor Mendel", "Charles Darwin", "Jean-Baptiste Lamarck", "Watson and Crick"],
        "answer": "Gregor Mendel"
    },
    {
        "id": 2,
        "question": "Who proposed the theory of natural selection?",
        "options": ["Gregor Mendel", "Charles Darwin", "Jean-Baptiste Lamarck", "Watson and Crick"],
        "answer": "Charles Darwin"
    },
    {
        "id": 3,
        "question": "Who is known for the Lamarckian theory of evolution?",
        "options": ["Gregor Mendel", "Charles Darwin", "Jean-Baptiste Lamarck", "Watson and Crick"],
        "answer": "Jean-Baptiste Lamarck"
    },
    {
        "id": 4,
        "question": "Which duo discovered the DNA double helix?",
        "options": ["Gregor Mendel", "Charles Darwin", "Jean-Baptiste Lamarck", "Watson and Crick"],
        "answer": "Watson and Crick"
    }
]

@app.get("/api/quiz")
def get_quiz():
    # Return questions without the answers
    return [{"id": q["id"], "question": q["question"], "options": q["options"]} for q in QUIZ_QUESTIONS]

@app.post("/api/quiz/submit")
def submit_quiz(submission: QuizSubmission):
    score = 0
    results = []
    for answer in submission.answers:
        question = next((q for q in QUIZ_QUESTIONS if q["id"] == answer.question_id), None)
        if question:
            is_correct = question["answer"] == answer.answer
            if is_correct:
                score += 1
            results.append({
                "question_id": answer.question_id,
                "is_correct": is_correct,
                "correct_answer": question["answer"]
            })
    return {"score": score, "results": results, "total": len(QUIZ_QUESTIONS)}

@app.get("/")
def read_root():
    return {"message": "Genetics Quiz API is running."}