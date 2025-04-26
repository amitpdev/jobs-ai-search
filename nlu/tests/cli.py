import requests
from requests.exceptions import ConnectionError
import json
from pprint import pprint

API_ENDPOINT = "http://localhost:5005/model/parse"
COLOR_GREEN = '\033[92m'
COLOR_RESET = '\033[0m'

def send_nlu_request(text):
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({"text": text})
    try:
        response = requests.post(API_ENDPOINT, headers=headers, data=data)
    except ConnectionError as e:
        raise e
    return response.json()

def process_input(text):
    try:
        response = send_nlu_request(text)
    except ConnectionError:
        print(f"ERROR: cannot connect to NLU server API at {API_ENDPOINT}")
        return []
    entities = response.get('entities', [])
    return entities

def output(entities):
    print(COLOR_GREEN + "Found entities:")
    pprint(entities, indent=2)
    print(COLOR_RESET)

def main():
    try:
        while True:
            print("Type your input and hit enter. Press Ctrl+C to exit.")
            input_text = input()
            if input_text:
                entities = process_input(input_text.strip())
                output(entities)

    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
