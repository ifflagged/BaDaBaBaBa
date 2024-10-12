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
        
        # 检查 Rule
        if re.search(r',\s*dIRECT\s*,\s*REJECT\s*,\s*dIRECT\s*,\s*REJECT', line_lower):
            rules['Rule'].append(line)
        
        # 针对 .sgmodule 文件的 URL Rewrite
        if '^http*' in line:
            if '- reject' in line or '$1 302' in line:
                rules['URL Rewrite'].append(line)
        
        # 针对 .plugin 文件的 Rewrite
        if '^http*' in line:
            if 'reject' in line or '302 $1' in line:
                rules['Rewrite'].append(line)
        
        # 检查 Script
        if 'pattern=' in line and 'script-path=' in line:
            rules['Script'].append(line)
        
        # 检查 MITM
        if 'hostname =' in line_lower:
            rules['MITM'].append(line)
    
    return rules

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()
    
    return extract_rules(file_content)

def save_extracted_data(rules, output_dir, module_type):
    for category, entries in rules.items():
        if entries:
            category_dir = os.path.join(output_dir, category)
            os.makedirs(category_dir, exist_ok=True)
            output_file = os.path.join(category_dir, f'{module_type}.txt')
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write('\n'.join(entries) + '\n')

def main(input_file, output_dir):
    # 处理指定的文件
    if os.path.isfile(input_file):
        rules = process_file(input_file)

        # 根据文件扩展名保存到相应的输出目录
        if input_file.endswith('.sgmodule'):
            save_extracted_data(rules, os.path.join(output_dir, 'Surge/2nd'), 'Surge')
        elif input_file.endswith('.plugin'):
            save_extracted_data(rules, os.path.join(output_dir, 'Loon/2nd'), 'Loon')
    else:
        print(f"Error: {input_file} is not a valid file.")

if __name__ == '__main__':
    input_file = 'Links/2nd-Convert.txt'  # 输入文件路径
    output_directory = 'Modules'  # 输出文件夹路径
    main(input_file, output_directory)