import textwrap
import json
from rules_loader import search_rules, load_rules, compute_idf, RulesEntry
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY

client = Anthropic(api_key=ANTHROPIC_API_KEY)


def format_rules_context(relevant_entries: list[RulesEntry]) -> str:
    formatted_context:str = ""
    for entry in relevant_entries:
        formatted_context += f"---\nRULE: {entry.title}\n{entry.content}\n"
        if entry.subcodexes is not None:
            for label, text in entry.subcodexes.items():
                formatted_context += f"  {label}: {text}\n"
    return formatted_context



def ask_rules_bot(entries:list[RulesEntry], question:str, idf_values: dict[str, float]) -> None:
    relevant_rulings = search_rules(entries, question, idf_values)
    formatted_rulings = format_rules_context(relevant_rulings)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system= textwrap.dedent("""
        You are a Sorcery: Contested Realm rules expert. 
        Answer using ONLY the rules provided below.
        If the answer isn't in the provided rules, say so.
        Output in a JSON format with Key: formatting.
        Only include the exceptions section if a specific exception exists. Never include it to state that no exceptions were found.
        Always include the rules section when your answer is based on the provided rules. Only omit it when the answer cannot be found in the provided rules.
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
        question = input("\nAsk a rules question (or 'quit' to exit): ")
        if question.lower() == "quit":
            break
        ask_rules_bot(entries, question, idf_values)