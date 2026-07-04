import datetime
import json
import subprocess

from config import EVAL_SAVE_PATH, RULES_CSV_PATH, TEST_QUESTION_PATH
from rules_bot import prepare_search_query
from rules_loader import compute_idf, load_rules, search_rules

if TEST_QUESTION_PATH is not None:
    with open(TEST_QUESTION_PATH, encoding='utf-8') as file:
        TEST_QUESTION_DATA:list = json.load(file)


def eval_retrieval() -> dict|None:
    if RULES_CSV_PATH is not None:
        # get time for save time data
        eval_time = datetime.datetime.now()
        # load entries from CSV
        entries = load_rules(RULES_CSV_PATH)
        # generate idf
        idf_values = compute_idf(entries)
        # initialise running totals for logging
        running_total_correct = 0
        running_total_expected = 0
        q_results:list[dict] = []
        # loop through JSON entries within test dataset once for each question
        for q in TEST_QUESTION_DATA:

            # prep keywords from question in test data
            question_relevant_words = prepare_search_query(q["question"])[0]
            # search using keywords retrieve entries based on TF-IDF 
            retrieved_entries = search_rules(entries, question_relevant_words, idf_values)
            # initialise lists containing correct keywords and retrieved entry titles
            # list comprehension of expected entries may be better?
            correct_entries:list[str] = []
            retrieved_entry_titles:list[str] = []
            # loop through retrieved entries
            for entry in retrieved_entries:
                retrieved_entry_titles.append(entry.title)

                if entry.title in q["expected_entries"]:
                    correct_entries.append(entry.title)
            running_total_correct += len(correct_entries)
            running_total_expected += len(q["expected_entries"])


            print(f"""{q['question']}\n{len(correct_entries)}/{len(q['expected_entries'])} correct\n
                  Expected: {q['expected_entries']}\nRetrieved: {retrieved_entry_titles}\n""")

            q_results.append({"question": q['question'], 
                              "score": {"correct": len(correct_entries), "expected": len(q['expected_entries'])}, 
                              "retrieved": retrieved_entry_titles, 
                              "expected": q['expected_entries']})

        percent = (running_total_correct / running_total_expected) * 100
        print(f"Total: {running_total_correct}/{running_total_expected} ({percent:.1f}%)")
        results_json:dict = {
            "timestamp": eval_time.strftime("%Y-%m-%d_%H-%M-%S"),
            "version": subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip('\n'),
            "scoring": {"total_correct": running_total_correct,"total_expected":running_total_expected},
            "method": "TF-IDF",
            "questions": q_results
        }
        return results_json
    else:
        print("Rules path not found")
        return None
    
def save_results(results_json:dict) -> None:
    if EVAL_SAVE_PATH is None:
        return
    EVAL_SAVE_PATH.mkdir(parents=True, exist_ok=True)
    with open(EVAL_SAVE_PATH/f"{results_json['timestamp']}.json", 'w', encoding='utf-8') as f:
        json.dump(results_json, f, indent=4)


if __name__ == "__main__":
    results = eval_retrieval()
    if results is not None:
        save_results(results)