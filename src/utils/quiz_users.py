from typing import List

import requests
import copy
import csv


def create_list(users: List[str], quiz: List[str]):
    """Create a dictionary mapping users to the quiz they are
    gonna do. There might be more quizes than users or more
    users than quizes."""

    result = {}
    # Assign a random quiz for each user. Try to avoid assigning
    # the same quiz to multiple users. If there are more users
    # than quizes, assign the same quiz to multiple users.

    quiz_copy = copy.deepcopy(quiz)
    for user in users:
        if len(quiz_copy) == 0:
            quiz_copy = copy.deepcopy(quiz)

        result[user] = quiz_copy.pop()

    return result


users = []
with open("src/utils/users.csv") as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        users.append(row[1])

quizes = []
with open("src/utils/quiz.csv") as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        quizes.append(row[1])

result = create_list(users[1:], quizes[1:])
for user, quiz in result.items():
    print(f"Assignig {user} to {quiz}")

    response = requests.post(
        "https://api.athenacrowdfunding.com/quiz/assign",
        json={"quiz_id": quiz, "user_stake_address": user},
    )

    print(response.status_code)
    print(response.json())
