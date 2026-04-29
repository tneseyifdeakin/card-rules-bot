import csv
import math
from dataclasses import dataclass


@dataclass
class RulesEntry:
    title:str
    content:str
    subcodexes:dict[str, str]


def load_rules(path: str) -> list[RulesEntry]:
    entries:list[RulesEntry] = []
    latest_entry:RulesEntry
    with open(path, "r", encoding="utf-8") as f:
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
    words = query.split()
    STOP_WORDS = {"the", "a", "an", "is", "are", "can", "how", "does", "do", "what", "when", "be", "i", "to", "it", "of", "in", "and", "or", "my"}
    cleaned = [normalise_word(word) for word in words]
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
    paired = [pair for pair in paired if pair[1] > (0.4 * max(scoreboard))]
    for content, scored in paired:
        print(f"Keyword: {content.title}: {scored}")
    # Sort by score, highest first
    paired.sort(key=lambda pair: pair[1], reverse=True)
    # Take top 5 and extract just the entries
    most_relevant = [pair[0] for pair in paired[:5]]
    print(key_words)
    return most_relevant


def compute_idf(entries: list[RulesEntry]) -> dict[str, float]:
    # initialise counter for unique words
    word_entry_counts = {}
    # loop through each entry building set of unique words from them
    for entry in entries:
        # using set because we only care if word exists not amount of a given word for idf calc 
        unique_words = set()
        unique_words.add(normalise_word(entry.title))
        # split str content into words and add each
        for word in entry.content.split():
            unique_words.add(normalise_word(word))

        # extract key and values from a dict item
        for key, values in entry.subcodexes.items():
            unique_words.add(normalise_word(key))
            for word in values.split():
                unique_words.add(normalise_word(word))

        # if at least 1 instance of a word within the entry exists, increment the counter by 1
        for word in unique_words:
            if word in word_entry_counts:
                word_entry_counts[word] += 1
            else:
                word_entry_counts[word] = 1

    idf_value = {}
    for word in word_entry_counts:
        idf_value[word] = math.log(len(entries)/word_entry_counts[word])
    return idf_value

# takes a str and outputs lowercase punctuation stripped str
def normalise_word(word:str) -> str :
    cleaned_word = word.strip("?.,!;:'\"").lower()
    return cleaned_word

if __name__ == "__main__":
    entries = load_rules("data/codex-27 Apr 2026.csv")
    idf_values = compute_idf(entries)
    print(idf_values["airborne"])
    print(idf_values["the"])

    # while True:
    #         question = input("\nAsk a rules question (or 'quit' to exit): ")
    #         if question.lower() == "quit":
    #             break
    #         relevant_rulings = search_rules(entries, question)
