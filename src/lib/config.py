import json


def load_config():
    with open("config.json", "r") as config:
        return json.load(config)
