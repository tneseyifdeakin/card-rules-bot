import datetime
import json
import subprocess

from config import CALIBRATION_SAVE_PATH, RULES_CSV_PATH, TEST_QUESTION_PATH
from rules_bot import ask_rules_bot
from rules_loader import compute_idf, load_rules, RulesEntry

if TEST_QUESTION_PATH is not None:
    with open(TEST_QUESTION_PATH, encoding='utf-8') as file:
        TEST_QUESTION_DATA:list = json.load(file)

def generate_calibration() -> dict|None:
    if RULES_CSV_PATH is None:
        return
    calibration_time = datetime.datetime.now()
    entries:list[RulesEntry] = load_rules(RULES_CSV_PATH)
    idf_values:dict[str, float] = compute_idf(entries)
    q_results:list[dict] = []

    for q in TEST_QUESTION_DATA:
        bot_output = ask_rules_bot(entries, q["question"], idf_values)
        bot_output["expected_answer"] = q["expected_answer"]
        q_results.append(bot_output)

    results_json:dict = {
                "timestamp": calibration_time.strftime("%Y-%m-%d_%H-%M-%S"),
                "version": subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip('\n'),
                "method": "TF-IDF",
                "questions": q_results,

            }
    return results_json
        
def save_calibration(results_json:dict) -> None:
    if CALIBRATION_SAVE_PATH is None:
        return
    CALIBRATION_SAVE_PATH.mkdir(parents=True, exist_ok=True)
    with open(CALIBRATION_SAVE_PATH/f"{results_json['timestamp']}.json", 'w', encoding='utf-8') as f:
        json.dump(results_json, f, indent=4)



if __name__ == "__main__":
    results = generate_calibration()
    if results is not None:
        save_calibration(results)