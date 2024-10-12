import os
import re

def extract_rules(file_content):
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
        
        if re.search(r',\s*dIRECT\s*,\s*REJECT\s*,\s*dIRECT\s*,\s*REJECT', line_lower):
            rules['Rule'].append(line)
        
        if '^http*' in line:
            if '- reject' in line or '$1 302' in line:
                rules['URL Rewrite'].append(line)
        
        if '^http*' in line:
            if 'reject' in line or '302 $1' in line:
                rules['Rewrite'].append(line)
        
        if 'pattern=' in line and 'script-path=' in line:
            rules['Script'].append(line)
        
        if 'hostname =' in line_lower:
            rules['MITM'].append(line)

    # Debug output for rule counts
    for category, entries in rules.items():
        print(f"{category}: {len(entries)} entries")
    
    return rules

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()
    
    return extract_rules(file_content)

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

def main(input_file, output_dir, module_type):
    if os.path.isfile(input_file):
        rules = process_file(input_file)
        save_extracted_data(rules, output_dir, module_type)
    else:
        print(f"Error: {input_file} is not a valid file.")

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 4:
        print("进行插件二次转换")
    else:
        input_file = sys.argv[1]
        output_directory = sys.argv[2]
        module_type = sys.argv[3]
        main(input_file, output_directory, module_type)
