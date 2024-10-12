import os
import re
import requests

def extract_rules(file_content, module_type):
    rules = {
        'Rule': [],
        'URL Rewrite': [],
        'Rewrite': [],
        'Script': [],
        'MITM': []
    }

    lines = file_content.splitlines()
    for line in lines:
        line_lower = line.lower()
        print(f"Processing line: {line}")  # Debug output

        # Rule extraction
        if re.search(r',\s*dIRECT\s*,\s*REJECT\s*,\s*dIRECT\s*,\s*REJECT', line_lower):
            rules['Rule'].append(line)
        
        # URL Rewrite or Rewrite extraction based on module type
        if '^http*' in line:
            if module_type == 'Surge':
                if '- reject' in line or '$1 302' in line:
                    rules['URL Rewrite'].append(line)
            elif module_type == 'Loon':
                if 'reject' in line or '302 $1' in line:
                    rules['Rewrite'].append(line)
        
        # Script extraction
        if 'pattern=' in line and 'script-path=' in line:
            rules['Script'].append(line)
        
        # MITM extraction
        if 'hostname =' in line_lower:
            rules['MITM'].append(line)

    # Debug output for rule counts
    for category, entries in rules.items():
        print(f"{category}: {len(entries)} entries")
    
    return rules

def fetch_and_process_links(links):
    all_rules = {
        'Rule': [],
        'URL Rewrite': [],
        'Rewrite': [],
        'Script': [],
        'MITM': []
    }

    for link in links:
        try:
            response = requests.get(link)
            response.raise_for_status()
            file_content = response.text
            module_type = 'Surge' if link.endswith('.sgmodule') else 'Loon'
            rules = extract_rules(file_content, module_type)

            for category, entries in rules.items():
                all_rules[category].extend(entries)

        except requests.RequestException as e:
            print(f"Error fetching {link}: {e}")

    return all_rules

def save_extracted_data(rules, output_dir, module_type):
    if module_type == 'Surge':
        base_path = os.path.join(output_dir, 'Surge/2nd/')
        extension = '.sgmodule'
    elif module_type == 'Loon':
        base_path = os.path.join(output_dir, 'Loon/2nd/')
        extension = '.plugin'
    else:
        print(f"Error: Unsupported module type '{module_type}'")
        return

    for category, entries in rules.items():
        if entries:
            category_dir = os.path.join(base_path, category)
            os.makedirs(category_dir, exist_ok=True)
            output_file = os.path.join(category_dir, f'{module_type}{extension}')
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write('\n'.join(entries) + '\n')
            print(f"Saved to: {output_file}")  # Debug output

def main(input_file, output_dir):
    if os.path.isfile(input_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            links = f.read().splitlines()
        
        rules = fetch_and_process_links(links)
        save_extracted_data(rules, output_dir, 'Surge')  # or 'Loon' based on your logic
    else:
        print(f"Error: {input_file} is not a valid file.")

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("Usage: python script.py input_file output_directory")
    else:
        input_file = sys.argv[1]
        output_directory = sys.argv[2]
        main(input_file, output_directory)
