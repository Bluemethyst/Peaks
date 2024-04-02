import json


def get_config():
    with open("config.json", "r") as config_file:
        return json.load(config_file)
