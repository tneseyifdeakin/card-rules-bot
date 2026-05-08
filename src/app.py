from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from config import RULES_CSV_PATH
from rules_bot import ask_rules_bot
from rules_loader import compute_idf, load_rules



app = FastAPI()
app.mount("/static", StaticFiles(directory="../static"), name="static")


if RULES_CSV_PATH is None:
    raise ValueError("RULES_CSV_PATH not set in .env")
entries = load_rules(RULES_CSV_PATH)
idf_values = compute_idf(entries)


class UserQuestion(BaseModel):
    user_question: str


@app.get("/")
def serve_frontend():
    return FileResponse("../static/index.html")

@app.post("/ask_question")
def ask_question(user_question: UserQuestion) -> dict:
    return ask_rules_bot(entries, user_question.user_question, idf_values)