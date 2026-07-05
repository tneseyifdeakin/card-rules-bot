import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

DATABASE_PATH = os.getenv("DATABASE_PATH")

RULES_CSV_PATH = os.getenv("RULES_CSV_PATH")

TEST_QUESTION_PATH = os.getenv("TEST_QUESTION_PATH")

EVAL_SAVE_PATH: Path | None = None
raw_save_path  = os.getenv("EVAL_SAVE_PATH")
if raw_save_path  is not None:
    EVAL_SAVE_PATH = Path(raw_save_path)

CALIBRATION_SAVE_PATH: Path | None = None
raw_save_path = os.getenv("CALIBRATION_SAVE_PATH")
if raw_save_path is not None:
    CALIBRATION_SAVE_PATH = Path(raw_save_path)
    

FIXTURE_SAVE_PATH: Path | None = None
raw_save_path = os.getenv("FIXTURE_SAVE_PATH")
if raw_save_path is not None:
    FIXTURE_SAVE_PATH = Path(raw_save_path)