import yaml
import csv
import pyperclip
import json
import re

def extract_number_from_string(string):
    number = re.findall(r'\d+', string)
    if number:
        return int(number[0])
    else:
        return None

def extract_step_api(data, stepIndex, flowIndex):
    flow = data['x-flows'][flowIndex]
    steps = flow['steps']
    step = steps[stepIndex]
    return step['api']

def compare_yaml_files(file1, file2):
    differences = {
        "missing_keys": [],
        "new_keys": [],
        "value_differences": []
    }

    def compare_dicts(d1, d2, path=""):
        missing_keys = set(d1.keys()) - set(d2.keys())
        new_keys = set(d2.keys()) - set(d1.keys())
        common_keys = set(d1.keys()) & set(d2.keys())

        for key in missing_keys:
            full_path = f"{path + '.' if path else ''}{key}"
            differences["missing_keys"].append(full_path)

        for key in new_keys:
            full_path = f"{path + '.' if path else ''}{key}"
            differences["new_keys"].append(full_path)

        for key in common_keys:
            full_path = f"{path + '.' if path else ''}{key}"
            if isinstance(d1[key], dict) and isinstance(d2[key], dict):
                compare_dicts(d1[key], d2[key], full_path)
            elif isinstance(d1[key], list) and isinstance(d2[key], list):
                compare_lists(d1[key], d2[key], full_path)
            elif d1[key] != d2[key]:
                differences["value_differences"].append((full_path, d1[key], d2[key]))

    def compare_lists(l1, l2, path=""):
        for index, (item1, item2) in enumerate(zip(l1, l2)):
            full_path = f"{path}[{index}]"
            if isinstance(item1, dict) and isinstance(item2, dict):
                compare_dicts(item1, item2, full_path)
            elif isinstance(item1, list) and isinstance(item2, list):
                compare_lists(item1, item2, full_path)
            elif item1 != item2:
                differences["value_differences"].append((full_path, item1, item2))

        if len(l1) > len(l2):
            for index in range(len(l2), len(l1)):
                full_path = f"{path}[{index}]"
                differences["missing_keys"].append(full_path)
        elif len(l2) > len(l1):
            for index in range(len(l1), len(l2)):
                full_path = f"{path}[{index}]"
                differences["new_keys"].append(full_path)

    print(f"Comparing {file1} and {file2}")

    with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
        try:
            data1 = yaml.safe_load(f1)
            data2 = yaml.safe_load(f2)
        except yaml.YAMLError as exc:
            print(f"Error loading YAML: {exc}")
            return

    # Compare the dictionaries and get the differences
    compare_dicts(data1, data2)
    pyperclip.copy(json.dumps(differences, indent=4))

    # Prepare data for CSV
    rows = []

    # Dictionary to store differences by API
    api_differences = {}

    def process_differences(diff_type, items):
        for item in items:
            if diff_type == "value_differences":
                path, old_value, new_value = item
                section = path.split('.')[0]
                second_element = path.split('.')[1] if len(path.split('.')) > 1 else ''
                fourth_element = path.split('.')[3] if len(path.split('.')) > 3 else ''
                
                if 'x-flows' in section:
                    second_element = extract_step_api(data1, extract_number_from_string(second_element), extract_number_from_string(section))
                
                api = second_element
                if api not in api_differences:
                    api_differences[api] = []

                if 'x-examples' in section:
                    api = fourth_element
                    rows.append({
                        'TYPE': 'Value Difference',
                        'SECTION': section,
                        'API': api,
                        'PATH': path,
                        'OLD VALUE': old_value,
                        'NEW VALUE': new_value,
                        'REMARKS': ''
                    })
                    
                
                if 'x-attributes' in section:
                    api = fourth_element
                    rows.append({
                        'TYPE': 'Value Difference',
                        'SECTION': section,
                        'API': api,
                        'PATH': path,
                        'OLD VALUE': old_value,
                        'NEW VALUE': new_value,
                        'REMARKS': ''
                    })
                else:
                    
                    rows.append({
                        'TYPE': 'Value Difference',
                        'SECTION': section,
                        'API': api,
                        'PATH': path,
                        'OLD VALUE': old_value,
                        'NEW VALUE': new_value,
                        'REMARKS': ''
                    })
                

            else:
                section = item.split('.')[0]
                second_element = item.split('.')[1] if len(item.split('.')) > 1 else ''
                fourth_element =item.split('.')[3] if len(item.split('.')) > 3 else ''
                if 'x-flows' in section:
                    second_element = extract_step_api(data1, extract_number_from_string(second_element), extract_number_from_string(section))
                
                api = second_element
                if api not in api_differences:
                    api_differences[api] = []
                    
                
               
                if 'x-examples' in section:
                     api = fourth_element
                     rows.append({
                        'TYPE': 'Missing Key' if diff_type == "missing_keys" else 'New Key',
                        'SECTION': section,
                        'API': api,
                        'PATH': item,
                        'OLD VALUE': '',
                        'NEW VALUE': '',
                        'REMARKS': ''
                    })
                if 'x-attributes' in section:
                    api = fourth_element
                    rows.append({
                        'TYPE': 'Missing Key' if diff_type == "missing_keys" else 'New Key',
                        'SECTION': section,
                        'API': api,
                        'PATH': item,
                        'OLD VALUE': '',
                        'NEW VALUE': '',
                        'REMARKS': ''
                        })
                else:
                    rows.append({
                        'TYPE': 'Missing Key' if diff_type == "missing_keys" else 'New Key',
                        'SECTION': section,
                        'API': api,
                        'PATH': item,
                        'OLD VALUE': '',
                        'NEW VALUE': '',
                        'REMARKS': ''
                    })

    print("Processing differences for CSV generation.")
    process_differences("missing_keys", differences["missing_keys"])
    process_differences("new_keys", differences["new_keys"])
    process_differences("value_differences", differences["value_differences"])

    # Flatten the differences grouped by API for CSV writing
    for api in api_differences:
        rows.extend(api_differences[api])

    # Write to CSV
    headers = ['TYPE','API',  'SECTION', 'PATH', 'OLD VALUE', 'NEW VALUE', 'REMARKS']
    output_file = 'yaml_comparison_results.csv'

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV file '{output_file}' generated successfully.")

# Example usage
file1 = 'build1.yaml'
file2 = 'build2.yaml'
compare_yaml_files(file1, file2)



