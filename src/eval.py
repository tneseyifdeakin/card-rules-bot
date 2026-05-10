import datetime
import json
import os
from config import TEST_QUESTION_PATH, RULES_CSV_PATH
from rules_bot import prepare_search_query
from rules_loader import search_rules, load_rules, compute_idf

if TEST_QUESTION_PATH is not None:
    with open(TEST_QUESTION_PATH, 'r', encoding='utf-8') as file:
        TEST_QUESTION_DATA:dict = json.load(file)

def eval_retrieval() -> None:
    if RULES_CSV_PATH is not None:
        entries = load_rules(RULES_CSV_PATH)
        idf_values = compute_idf(entries)
        running_total_correct = 0
        running_total_expected = 0
        for q in TEST_QUESTION_DATA:
            correct_keywords:list[str] = []
            retrieved_keywords:list[str] = []
            question_relevant_words = prepare_search_query(q["question"])[0]
            retrieved_entries = search_rules(entries, question_relevant_words, idf_values)
            for entry in retrieved_entries:
                retrieved_keywords.append(entry.title)
                if entry.title in q["expected_entries"]:
                    correct_keywords.append(entry.title)
            running_total_correct += len(correct_keywords)
            running_total_expected += len(q["expected_entries"])
            print(f"{q['question']}\n{len(correct_keywords)}/{len(q['expected_entries'])} correct\nExpected: {q['expected_entries']}\nRetrieved: {retrieved_keywords}\n")
        percent = (running_total_correct / running_total_expected) * 100
        print(f"Total: {running_total_correct}/{running_total_expected} ({percent:.1f}%)")
    else:
        print("Rules path not found")
    


if __name__ == "__main__":
    eval_retrieval()