import os
import re
import requests

def extract_rules(content, file_type):
    rules = []
    url_rewrites = []  # 修正为 url_rewrites
    rewrites = []
    scripts = []
    mitm = []

    # 正则表达式匹配，增加了不区分大小写
    rule_pattern = re.compile(r',\s*DIRECT|,\s*REJECT', re.IGNORECASE)
    url_rewrite_pattern = re.compile(r'^\^http.*?(- reject|\$1 302)', re.IGNORECASE)
    rewrite_pattern = re.compile(r'^\^http.*?(reject|\$1 302)', re.IGNORECASE)
    script_pattern = re.compile(r'pattern=|script-path=', re.IGNORECASE)
    mitm_pattern = re.compile(r'Hostname\s*=', re.IGNORECASE)

    for line in content.splitlines():
        line = line.strip()
        print(f"Processing line: {line}")  # 调试信息
        if not line:
            continue  # 跳过空行
        if rule_pattern.search(line):
            rules.append(line)
            print(f"Matched Rule: {line}")  # 调试信息
        if file_type == 'sgmodule':
            if url_rewrite_pattern.search(line):
                url_rewrites.append(line)  # 匹配 URL Rewrite
                print(f"Matched URL Rewrite: {line}")  # 调试信息
        elif file_type == 'plugin' and rewrite_pattern.search(line):
            rewrites.append(line)
            print(f"Matched Rewrite: {line}")  # 调试信息
        if script_pattern.search(line):
            scripts.append(line)
            print(f"Matched Script: {line}")  # 调试信息
        if mitm_pattern.search(line):
            mitm.append(line)
            print(f"Matched MITM: {line}")  # 调试信息

    return rules, url_rewrites, rewrites, scripts, mitm  # 返回 url_rewrites

def process_file(content, file_type):
    print(f"Processing {file_type} content...")

    rules, url_rewrites, rewrites, scripts, mitm = extract_rules(content, file_type)

    print(f"Extracted Rules: {rules}")
    print(f"Extracted URL Rewrites: {url_rewrites}")
    print(f"Extracted Rewrites: {rewrites}")
    print(f"Extracted Scripts: {scripts}")
    print(f"Extracted MITM: {mitm}")

    return {
        'rules': rules,
        'url_rewrites': url_rewrites,  # 确保返回 URL rewrites
        'rewrites': rewrites,
        'scripts': scripts,
        'mitm': mitm
    }

def save_to_file(data, output_path, file_type):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        if file_type == 'sgmodule':
            f.write('[Rule]\n' + '\n'.join(data['rules']) + '\n')
            f.write('[URL Rewrite]\n' + '\n'.join(data['url_rewrites']) + '\n')  # 使用正确的字段
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
