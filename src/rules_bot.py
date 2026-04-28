from rules_loader import search_rules, load_rules, RulesEntry
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



def ask_rules_bot(entries:list[RulesEntry], question:str) -> None:
    relevant_rulings = search_rules(entries, question)
    formatted_rulings = format_rules_context(relevant_rulings)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system="You are a Sorcery: Contested Realm rules expert. Answer using ONLY the rules provided below. If the answer isn't in the provided rules, say so.",
        messages=[
        {"role": "user", "content": f"{formatted_rulings}\n\nQuestion: {question}"}
        ],
    )
    print(message.content[0].text) # type: ignore
    print(f"\nTokens used — input: {message.usage.input_tokens}, output: {message.usage.output_tokens}")

if __name__ == "__main__":
    entries = load_rules("data/codex-27 Apr 2026.csv")
    while True:
        question = input("\nAsk a rules question (or 'quit' to exit): ")
        if question.lower() == "quit":
            break
        ask_rules_bot(entries, question)