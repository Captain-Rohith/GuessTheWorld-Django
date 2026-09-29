from collections import Counter
from typing import List, Dict, Any


def evaluate_wordle_guess(target_word: str, guess_word: str) -> List[Dict[str, str]]:
    target = target_word.strip().upper()
    guess = guess_word.strip().upper()

    if len(target) != 5 or len(guess) != 5:
        raise ValueError("Both target_word and guess_word must be exactly 5 letters long.")

    result_statuses = [None] * 5
    target_letter_counts = Counter(target)

    for i in range(5):
        if guess[i] == target[i]:
            result_statuses[i] = "green"
            target_letter_counts[guess[i]] -= 1

    for i in range(5):
        if result_statuses[i] is None:
            char = guess[i]
            if target_letter_counts.get(char, 0) > 0:
                result_statuses[i] = "yellow"
                target_letter_counts[char] -= 1
            else:
                result_statuses[i] = "grey"

    return [
        {"letter": guess[i], "status": result_statuses[i]}
        for i in range(5)
    ]


def compute_keyboard_statuses(evaluated_attempts: List[List[Dict[str, str]]]) -> Dict[str, str]:
    priority = {"green": 3, "yellow": 2, "grey": 1}
    keyboard_map = {}

    for attempt in evaluated_attempts:
        for item in attempt:
            letter = item["letter"]
            status = item["status"]
            current_status = keyboard_map.get(letter)
            if current_status is None or priority[status] > priority.get(current_status, 0):
                keyboard_map[letter] = status

    return keyboard_map
