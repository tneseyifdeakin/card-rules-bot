import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

DATABASE_PATH = os.getenv("DATABASE_PATH")

RULES_CSV_PATH = os.getenv("RULES_CSV_PATH")

TEST_QUESTION_PATH = os.getenv("TEST_QUESTION_PATH")