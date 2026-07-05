import datetime
import json
import subprocess
import textwrap
from config import CALIBRATION_SAVE_PATH, FIXTURE_SAVE_PATH ,RULES_CSV_PATH, TEST_QUESTION_PATH
from rules_bot import ask_rules_bot, client
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



def generate_fixture() -> None:
    if CALIBRATION_SAVE_PATH is None or FIXTURE_SAVE_PATH is None:
        return 
    
    files = [
    f for f in CALIBRATION_SAVE_PATH.glob("*.json")
    if not f.name.startswith(("labels_", "synthetic_"))
    ]

    try:
        calibration_filepath = max(files)
    except ValueError:
        print("No calibration files found in ", CALIBRATION_SAVE_PATH)
        return
    with open(calibration_filepath, encoding = "utf-8") as calibration_file:
        calibration_data:dict = json.load(calibration_file)

    content:str = f"question: {calibration_data["questions"][0]["question"]}\nanswer: {calibration_data["questions"][0]["answer"]}"
    if "rules" in calibration_data["questions"][0]:
        content += f"\nrules: {calibration_data["questions"][0]['rules']}"
    if "exceptions" in calibration_data["questions"][0]:
        content += f"\nexceptions: {calibration_data["questions"][0]['exceptions']}"
    content += f"\nexpected answer: {calibration_data["questions"][0]['expected_answer']}"


    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        temperature=0,
        system= textwrap.dedent("""
        You are a Judge for a Sorcery: Contested Realm rules bot. 
        You will evaluate correctness based on the input question, rules bot you are judging's answer and expected answer
        answer: must match expected answer
        AND rules: must support answer
        AND exceptions: must not contradict answer as a general claim
        Do not include markdown fencing in your response.
        Order your response as follows: Justification then Verdict.
        Verdict should be binary 1 if correctness is true or 0 if correctness is false e.g. verdict: 0
        Output your response in a JSON format
        {
        "justification": "Insert justification here.",
        "verdict": 1
        }
        """),
        messages=[{"role": "user", "content": content}])
    
    result:str = message.content[0].text # type: ignore
    print(f"input: {message.usage.input_tokens}, output: {message.usage.output_tokens}")
    FIXTURE_SAVE_PATH.mkdir(parents=True, exist_ok=True)
    with open(FIXTURE_SAVE_PATH/"correctness_fixture_raw.txt", 'w', encoding='utf-8') as f:
        f.write(result)



if __name__ == "__main__":

    # results = generate_calibration()
    # if results is not None:
    #     save_calibration(results)


    generate_fixture()