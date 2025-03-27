import json

def find_value_index(dictionary, target_value):
    # Enumerate over the dictionary items to find the index of the value
    for index, (key, value) in enumerate(dictionary.items()):
        if value == target_value:
            return index, key
    return -1, None  # Return -1 and None if the value is not found

def load_json_file(file_path):
    # Load the JSON file and return the dictionary
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

# Path to your JSON file
json_file_path = 'first100.json'

# Value to find
value_to_find = 899751

# Load JSON data from file
json_data = load_json_file(json_file_path)

# Get the index and key of the value
index, key = find_value_index(json_data, value_to_find)

# Output the result
if index != -1:
    print(f"The value '{value_to_find}' is associated with key '{key}' at index {index}.")
else:
    print(f"The value '{value_to_find}' was not found in the JSON dictionary.")
