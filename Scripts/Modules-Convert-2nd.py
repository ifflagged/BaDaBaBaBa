import os
import re
import requests

def extract_rules(content, file_type):
    rules, url_rewrites, rewrites, scripts, mitm = [], [], [], [], []

    patterns = {
        'rules': re.compile(r',\s*DIRECT|,\s*REJECT', re.IGNORECASE),
        'url_rewrites': re.compile(r'^\^http.*?(- reject|\$1 302)', re.IGNORECASE) if file_type == 'sgmodule' else None,
        'rewrites': re.compile(r'^\^http.*?(reject|\$1 302)', re.IGNORECASE) if file_type == 'plugin' else None,
        'scripts': re.compile(r'pattern=|script-path=', re.IGNORECASE),
        'mitm': re.compile(r'Hostname\s*=', re.IGNORECASE)
    }

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        for key, pattern in patterns.items():
            if pattern and pattern.search(line):
                locals()[key].append(line)
                print(f"Matched {key.capitalize()}: {line}")

    return rules, url_rewrites, rewrites, scripts, mitm

def process_file(content, file_type):
    print(f"Processing {file_type} content...")
    extracted_data = extract_rules(content, file_type)
    return {key: value for key, value in zip(['rules', 'url_rewrites', 'rewrites', 'scripts', 'mitm'], extracted_data)}

def save_to_file(data, output_path, file_type):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    sections = {
        'sgmodule': ['[Rule]', data['rules'], '[URL Rewrite]', data['url_rewrites'], '[Script]', data['scripts'], '[MITM]', data['mitm']],
        'plugin': ['[Rule]', data['rules'], '[Rewrite]', data['rewrites'], '[Script]', data['scripts'], '[MITM]', data['mitm']]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(f"{section}\n{'\n'.join(lines)}" for section, lines in zip(sections[file_type][::2], sections[file_type][1::2])) + '\n')

def download_file(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def main():
    input_file = os.getenv('INPUT_FILE')
    output_dirs = {
        'sgmodule': 'Modules/Surge/2nd/',
        'plugin': 'Modules/Loon/2nd/'
    }

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            links = [link.strip() for link in f if link.strip()]
    except Exception as e:
        print(f"Error reading input file: {e}")
        return

    for link in links:
        print(f"Processing link: {link}")
        file_type = 'sgmodule' if link.endswith('.sgmodule') else 'plugin' if link.endswith('.plugin') else None

        if file_type:
            try:
                content = download_file(link)
                data = process_file(content, file_type)
                save_to_file(data, os.path.join(output_dirs[file_type], os.path.basename(link)), file_type)
            except Exception as e:
                print(f"Error processing {link}: {e}")

    print("Processing completed.")

if __name__ == '__main__':
    main()
