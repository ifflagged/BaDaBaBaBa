import os
import re

def extract_rules(content, file_type):
    rules = []
    rewrites = []
    scripts = []
    mitm = []

    rule_pattern = re.compile(r'(?i)\bDIRECT\b|\bREJECT\b')
    rewrite_pattern = re.compile(r'^\^http.*?(- reject|\$1 302)', re.IGNORECASE)
    script_pattern = re.compile(r'pattern=|script-path=')
    mitm_pattern = re.compile(r'(?i)Hostname\s*=')

    for line in content.splitlines():
        if rule_pattern.search(line):
            rules.append(line.strip())
        if file_type == 'sgmodule' and rewrite_pattern.search(line):
            rewrites.append(line.strip())
        elif file_type == 'plugin' and rewrite_pattern.search(line):
            rewrites.append(line.strip())
        if script_pattern.search(line):
            scripts.append(line.strip())
        if mitm_pattern.search(line):
            mitm.append(line.strip())

    return rules, rewrites, scripts, mitm

def process_file(file_path):
    file_type = file_path.split('.')[-1]
    print(f"Processing file: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"File content:\n{content}\n")

    rules, rewrites, scripts, mitm = extract_rules(content, file_type)

    print(f"Extracted Rules: {rules}")
    print(f"Extracted Rewrites: {rewrites}")
    print(f"Extracted Scripts: {scripts}")
    print(f"Extracted MITM: {mitm}")

    return {
        'rules': rules,
        'rewrites': rewrites,
        'scripts': scripts,
        'mitm': mitm
    }

def save_to_file(data, output_path, file_type):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        if file_type == 'sgmodule':
            f.write('[Rule]\n' + '\n'.join(data['rules']) + '\n')
            f.write('[URL Rewrite]\n' + '\n'.join(data['rewrites']) + '\n')
            f.write('[Script]\n' + '\n'.join(data['scripts']) + '\n')
            f.write('[MITM]\n' + '\n'.join(data['mitm']) + '\n')
        else:
            f.write('[Rule]\n' + '\n'.join(data['rules']) + '\n')
            f.write('[Rewrite]\n' + '\n'.join(data['rewrites']) + '\n')
            f.write('[Script]\n' + '\n'.join(data['scripts']) + '\n')
            f.write('[MITM]\n' + '\n'.join(data['mitm']) + '\n')

def main():
    input_dir = 'Modules/Surge/2nd/'
    output_surge_dir = 'Modules/Surge/2nd/'
    output_loon_dir = 'Modules/Loon/2nd/'

    print("Listing input files...")
    for filename in os.listdir(input_dir):
        print(f"Found file: {filename}")
        if filename.endswith('.sgmodule'):
            data = process_file(os.path.join(input_dir, filename))
            save_to_file(data, os.path.join(output_surge_dir, filename), 'sgmodule')
        elif filename.endswith('.plugin'):
            data = process_file(os.path.join(input_dir, filename))
            save_to_file(data, os.path.join(output_loon_dir, filename), 'plugin')

if __name__ == '__main__':
    main()
