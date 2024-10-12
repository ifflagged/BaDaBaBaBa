import os
import re
import requests

def extract_rules(content, file_type):
    rules = []
    rewrites = []
    scripts = []
    mitm = []

    # 正则表达式匹配
    rule_pattern = re.compile(r'(?i)(,\s*DIRECT|,\s*REJECT)')
    rewrite_pattern = re.compile(r'^\^http.*?(- reject|\$1 302)', re.IGNORECASE)
    script_pattern = re.compile(r'pattern=|script-path=')
    mitm_pattern = re.compile(r'(?i)Hostname\s*=')

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue  # 跳过空行
        if rule_pattern.search(line):
            rules.append(line)
        if file_type == 'sgmodule' and rewrite_pattern.search(line):
            rewrites.append(line)
        elif file_type == 'plugin' and rewrite_pattern.search(line):
            rewrites.append(line)
        if script_pattern.search(line):
            scripts.append(line)
        if mitm_pattern.search(line):
            mitm.append(line)

    return rules, rewrites, scripts, mitm

def process_file(content, file_type):
    print(f"Processing {file_type} content...")

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

def download_file(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def main():
    input_file = os.getenv('INPUT_FILE')  # 从环境变量获取输入文件路径
    output_surge_dir = 'Modules/Surge/2nd/'
    output_loon_dir = 'Modules/Loon/2nd/'

    print(f"Reading links from {input_file}...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            links = f.readlines()
    except Exception as e:
        print(f"Error reading input file: {e}")
        return

    for link in links:
        link = link.strip()
        if not link:
            continue  # 跳过空行
        print(f"Processing link: {link}")
        if link.endswith('.sgmodule'):
            try:
                content = download_file(link)
                data = process_file(content, 'sgmodule')
                save_to_file(data, os.path.join(output_surge_dir, os.path.basename(link)), 'sgmodule')
            except Exception as e:
                print(f"Error processing {link}: {e}")
        elif link.endswith('.plugin'):
            try:
                content = download_file(link)
                data = process_file(content, 'plugin')
                save_to_file(data, os.path.join(output_loon_dir, os.path.basename(link)), 'plugin')
            except Exception as e:
                print(f"Error processing {link}: {e}")

    print("Processing completed.")

if __name__ == '__main__':
    main()
