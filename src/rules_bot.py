import json
import re
import sqlite3
import textwrap

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, DATABASE_PATH
from rules_loader import RulesEntry, compute_idf, load_rules, search_rules

client = Anthropic(api_key=ANTHROPIC_API_KEY)


def extract_card_refs(text: str) -> list[str]:
    return re.findall(r"\[\[(.+?)\]\]", text)

def format_rules_context(relevant_entries: list[RulesEntry]) -> str:
    formatted_context:str = ""
    cards_in_data = []
    for entry in relevant_entries:
        # += as none will not be added with this
        formatted_context += f"---\nRULE: {entry.title}\n{entry.content}\n"
        # checks for cards in [[]] format within content text
        cards_in_data += extract_card_refs(entry.content)
        # check if subcodexes aexist
        if entry.subcodexes is not None:
            # loop through subcodex info an add to str
            for label, text in entry.subcodexes.items():
                formatted_context += f"  {label}: {text}\n"
                # += as none will not be added with this
                # checks for cards in [[]] format within subcodex text
                cards_in_data += extract_card_refs(text)

    for card in set(cards_in_data):
        card_info = get_card_info(card)
        if card_info is not None:
            formatted_context += f"\n---\nCARD: {card}\n{json.dumps(card_info)}\n"

    return formatted_context

def get_card_info(card_name:str) -> dict | None:
    if DATABASE_PATH is None:
        return None
    with sqlite3.connect(DATABASE_PATH) as conn:
        card_info = conn.execute("""
            SELECT  name,
                    rarity,
                    description,
                    cost,
                    threshold, 
                    element, 
                    type_line, 
                    card_category, 
                    card_type, 
                    card_subtype, 
                    power_rating, 
                    defense_power
            FROM cards
            WHERE name = ?

        """, 
        (card_name,)).fetchone()
        if card_info is None:
            return None
        else:
            keys = ["name", 
                    "rarity", 
                    "description", 
                    "cost", 
                    "threshold", 
                    "element", 
                    "type_line", 
                    "card_category", 
                    "card_type", 
                    "card_subtype", 
                    "power_rating", 
                    "defense_power"]
            return dict(zip(keys, card_info, strict=True))
    

    

def ask_rules_bot(entries:list[RulesEntry], question:str, idf_values: dict[str, float]) -> None:
    # removes card name from search question text so it isn't used as keyword
    question_relevant_words = re.sub(r"\[\[.+?\]\]", "", question)
    # extracts info on cards referenced in [[]] witin the question and saves as list
    cards_in_question = extract_card_refs(question)
    # initialise dict of card data
    card_data = {}
    # loops through each card name in extracted from question cards list
    for card in cards_in_question:
        # calls query to get info on current card within list
        info = get_card_info(card)
        # if query isn't none then map info to card_data dict[card name]
        if info is not None:
            card_data[card] = info
            # appends card info into search for ruling and removes <br> formatting from card description
            question_relevant_words += " " + re.sub(r"<br>", " ", info["description"])
    relevant_rulings = search_rules(entries, question_relevant_words, idf_values)
    formatted_rulings = format_rules_context(relevant_rulings)
    for card in card_data:
        if card not in formatted_rulings:
            formatted_rulings += f"\n---\nCARD: {card}\n{json.dumps(card_data[card])}\n"
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system= textwrap.dedent("""
        You are a Sorcery: Contested Realm rules expert. 
        Answer using ONLY the rules provided below.
        If the answer isn't in the provided rules, say so.
        Output in a JSON format with Key: formatting.
        Only include the exceptions section if a specific exception exists.
        Never include it to state that no exceptions were found.
        Always include the rules section when your answer is based on the provided rules. 
        Only omit it when the answer cannot be found in the provided rules.
        Do not include markdown fencing in your response.
        Ensure information isn't repeated between sections and is within the most relevant section.
        {
        "answer":
        "Insert single sentence answer to the question here.",
        "rules":
        "Insert an array of single sentences per relevant rule here.",
        "exceptions":
        "Insert an array of single sentences per exception to the answer/rule here."
        }
        """),
        messages=[
        {"role": "user", "content": f"{formatted_rulings}\n\nQuestion: {question}"}
        ],
    )
    # print(message.content[0].text) # type: ignore
    json_parser(message.content[0].text) # type: ignore
    print(f"\nTokens used — input: {message.usage.input_tokens}, output: {message.usage.output_tokens}")



def json_parser(bot_response: str) -> None:
    cleaned_response = bot_response.replace("```json", "").replace("```", "").strip()
    output:str = ""
    try:
        response_json = json.loads(cleaned_response)
        if "answer" in response_json:
            output += f"Answer:\n{response_json['answer']}\n"
        if "rules" in response_json:
            output += "\nRules:\n"
            for rule in response_json['rules']:
                output += f"{rule}\n"
        if "exceptions" in response_json:
            output += "\nExceptions:\n"
            for exception in response_json['exceptions']:
                output += f"{exception}\n"
        print(output)
    except json.JSONDecodeError as e:
        print(f"Failed to parse response: {e}")
        print(f"Raw response: {cleaned_response}")
        



if __name__ == "__main__":
    entries = load_rules("data/codex-27 Apr 2026.csv")
    idf_values = compute_idf(entries)

    while True:
        question = input("\nAsk a rules question (use [[Card Name]] to reference cards, or 'quit' to exit): ")
        if question.lower() == "quit":
            break
        ask_rules_bot(entries, question, idf_values)