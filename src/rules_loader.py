import csv
from dataclasses import dataclass


@dataclass
class RulesEntry:
    title:str
    content:str
    subcodexes:dict[str, str]


def load_rules(path: str) -> list[RulesEntry]:
    entries:list[RulesEntry] = []
    latest_entry:RulesEntry
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["title"] != "":
                latest_entry = RulesEntry(row["title"], row["content"], subcodexes={})
                entries.append(latest_entry)
            else:
                new_dict = row["subcodexes"].split(":", 1)
                latest_entry.subcodexes[new_dict[0]] = new_dict[1]
    return entries




def search_rules(entries:list[RulesEntry], query:str) -> list[RulesEntry]:
    most_relevant:list[RulesEntry] = []
    words = query.lower().split()
    STOP_WORDS = {"the", "a", "an", "is", "are", "can", "how", "does", "do", "what", "when", "be", "i", "to", "it", "of", "in", "and", "or", "my"}
    cleaned = [word.strip("?.,!;:'\"") for word in words]
    key_words = [word for word in cleaned if word not in STOP_WORDS]
    scoreboard:list[int] = []
    for entry in entries:
        score = 0
        for word in key_words:
            if word in entry.title.lower():
                if word == entry.title.lower():
                    score += 10
                else: score += 3
            if word in entry.content.lower():
                score += 1
            # Check subcodex labels (keys)
            for label in entry.subcodexes:
                if word in label.lower():
                    score += 2

            # Check subcodex content (values)
            for text in entry.subcodexes.values():
                if word in text.lower():
                    score += 1
        scoreboard.append(score)
    # Pair them up into a list of tuples
    paired = list(zip(entries, scoreboard))
    # Filter out zero scores
    paired = [pair for pair in paired if pair[1] > 0]
    # Sort by score, highest first
    paired.sort(key=lambda pair: pair[1], reverse=True)
    # Take top 5 and extract just the entries
    most_relevant = [pair[0] for pair in paired[:5]]
    print(key_words)
    return most_relevant



if __name__ == "__main__":
    entries = load_rules("data/codex-27 Apr 2026.csv")
    # for entry in entries:
    #     if entry.title == "Casting Spells":
    #         print(entry.title)
    #         print(entry.content[:100])
    #         for label, text in entry.subcodexes.items():
    #             print(f"  {label}: {text[:80]}...")
    #         break
    queries = [
        "how does airborne work?",
        "can I cast a minion?",
        "what happens when a card is banished?"
    ]
    for q in queries:
        print(f"\nQuery: {q}")
        results = search_rules(entries, q)
        for entry in results:
            print(f"  → {entry.title}")