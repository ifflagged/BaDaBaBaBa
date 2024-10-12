import os
import requests

# 定义需要的部分
required_sections = ['[Rule]', '[Rewrite]', '[Script]', '[MITM]']

# 下载文件函数
def download_file(url):
    response = requests.get(url)
    return response.text if response.status_code == 200 else None

# 检查和分类各部分内容
def parse_sections(content):
    sections = {section: '' for section in required_sections}
    current_section = None
    
    for line in content.splitlines():
        line = line.strip()
        if line in required_sections:
            current_section = line
        elif current_section:
            sections[current_section] += line + '\n'
    
    return sections

# 检查和添加缺失部分
def check_and_add_sections(sections):
    modified_content = ''
    for section in required_sections:
        modified_content += section + '\n'
        modified_content += sections[section] + '\n'
        if not sections[section]:  # 如果该部分没有内容，添加一个占位符
            modified_content += '# Placeholder for ' + section + '\n\n'
    
    return modified_content

# 保存文件
def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# 处理模块
def process_module(url, output_directory):
    content = download_file(url)
    if content:
        sections = parse_sections(content)
        modified_content = check_and_add_sections(sections)
        output_filename = os.path.basename(url)  # 提取文件名
        output_path = os.path.join(output_directory, output_filename)  # 生成输出文件路径
        save_file(output_path, modified_content)
        print(f"Processed and saved: {output_path}")
    else:
        print(f"Failed to download: {url}")

# 主函数
def main(urls_file_path):
    # 创建输出目录（如果不存在）
    surge_directory = 'Modules/Surge/2nd/'
    loon_directory = 'Modules/Loon/2nd/'
    os.makedirs(surge_directory, exist_ok=True)
    os.makedirs(loon_directory, exist_ok=True)

    # 从文件读取 URLs
    with open(urls_file_path, 'r', encoding='utf-8') as urls_file:
        module_urls = [line.strip() for line in urls_file if line.strip()]  # 读取非空行

    # 处理每个 URL
    for url in module_urls:
        if url.endswith('.sgmodule'):
            process_module(url, surge_directory)
        elif url.endswith('.plugin'):
            process_module(url, loon_directory)

# 示例使用
if __name__ == "__main__":
    urls_file_path = 'Links/2nd-Convert.txt'  # 设置保存路径
    main(urls_file_path)
