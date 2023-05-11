import requests
import csv


endpoint = "https://api.athenacrowdfunding.com/quiz/powerup"


quiz_assignments = []
with open("src/utils/quiz_assignment.csv") as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        quiz_assignments.append(row[1])

for quiz_assignment in quiz_assignments[1:]:
    print(f"Assigning powerups for {quiz_assignment}")

    response = requests.post(f"{endpoint}/{quiz_assignment}/create/get_hints", json={})
    if response.status_code != 200:
        print(response.json())
        raise Exception(f"Failed to assign get_hints for {quiz_assignment}")
    
    response = requests.post(
        f"{endpoint}/{quiz_assignment}/create/skip_question", json={}
    )
    if response.status_code != 200:
        print(response.json())
        raise Exception(f"Failed to assign skip_question for {quiz_assignment}")
    
    response = requests.post(
        f"{endpoint}/{quiz_assignment}/create/eliminate_half", json={}
    )
    if response.status_code != 200:
        print(response.json())
        raise Exception(f"Failed to assign eliminate_half for {quiz_assignment}")
