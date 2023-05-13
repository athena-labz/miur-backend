import csv
import json
import requests

from typing import List

# def parse_option(options: List[str]) -> List[str]:
#     letter = {
#         0: "a)",
#         1: "b)",
#         2: "c)",
#         3: "d)",
#         4: "e)",
#         5: "f)",
#         6: "g)",
#         7: "h)",
#     }

#     options = filter(lambda x: x != "", options)
#     return [f"{letter[i]} {option.capitalize()}" for (i, option) in enumerate(options)]


# with open("src/utils/quiz_responses.csv", newline="") as csvfile:
#     reader = csv.reader(csvfile)
#     questions = []
#     for row in reader:
#         questions.append(
#             {
#                 "timestamp": row[0],
#                 "name": row[1],
#                 "question_1": {
#                     "question": row[2],
#                     "options": parse_option(row[3].split("\n")),
#                     "answer": row[4],
#                     "hint": row[5],
#                 },
#                 "question_2": {
#                     "question": row[6],
#                     "options": parse_option(row[7].split("\n")),
#                     "answer": row[8],
#                     "hint": row[9],
#                 },
#                 "question_3": {
#                     "question": row[10],
#                     "options": parse_option(row[11].split("\n")),
#                     "answer": row[12],
#                     "hint": row[13],
#                 },
#                 "question_4": {
#                     "question": row[14],
#                     "options": parse_option(row[15].split("\n")),
#                     "answer": row[16],
#                     "hint": row[17],
#                 },
#                 "question_5": {
#                     "question": row[18],
#                     "options": parse_option(row[19].split("\n")),
#                     "answer": row[20],
#                     "hint": row[21],
#                 },
#                 "question_6": {
#                     "question": row[22],
#                     "options": parse_option(row[23].split("\n")),
#                     "answer": row[24],
#                     "hint": row[25],
#                 },
#                 "question_7": {
#                     "question": row[26],
#                     "options": parse_option(row[27].split("\n")),
#                     "answer": row[28],
#                     "hint": row[29],
#                 },
#                 "question_8": {
#                     "question": row[30],
#                     "options": parse_option(row[31].split("\n")),
#                     "answer": row[32],
#                     "hint": row[33],
#                 },
#                 "question_9": {
#                     "question": row[34],
#                     "answer": row[35],
#                     "hint": row[36],
#                 },
#                 "question_10": {
#                     "question": row[37],
#                     "answer": row[38],
#                     "hint": row[39],
#                 },
#             }
#         )

# with open("src/utils/quiz.json", "w") as file:
#     file.write(json.dumps(questions))

with open("src/utils/quiz.json", "r") as file:
    quizes = json.loads(file.read())

    for quiz in quizes:
        print(f"Posting quiz for {quiz['name']}")

        body = {
            "creator_name": quiz["name"],
            "questions": []
        }
        for question in [quiz[f"question_{i+1}"] for i in range(0, 10)]:
            if "options" in question:
                body["questions"].append({
                    "question": question["question"],
                    "answers": question["options"],
                    "right_answer": int(question["answer"]),
                    "hints": [question["hint"]],
                })
            else:
                if question["answer"].lower() != "true" and question["answer"].lower() != "false":
                    raise Exception(f"Invalid answer for {question['question']} - {question['answer']}")
                
                body["questions"].append({
                    "question": question["question"],
                    "answers": ["a) True", "b) False"],
                    "right_answer": 0 if question["answer"].lower() == "true" else 1,
                    "hints": [question["hint"]],
                })

        response = requests.post(
            "https://api.athenacrowdfunding.com/quiz/create",
            json=body
        )

        print(response.status_code)
        print(response.json())
