import requests
import os
import sys

def extract_section(content, section_name):
    lines = content.splitlines()
    in_section = False
    section_lines = []

    for line in lines:
        # 检查是否进入特定部分
        if line.startswith(f"[{section_name}]"):
            in_section = True
        elif line.startswith("[") and in_section:
            break
        elif in_section and (not line.startswith("#")):  # 忽略注释行
            section_lines.append(line.strip())  # 去除前后空格
    
    return section_lines

def merge_modules(input_file):
    with open(input_file, 'r') as f:
        module_urls = f.read().splitlines()

    rules = []
    rewrites = []
    scripts = []
    mitm_hosts = []

    for module_url in module_urls:
        print(f"Processing module: {module_url}")  # 调试信息
        response = requests.get(module_url)
        
        if response.status_code != 200:
            print(f"Failed to download {module_url}: {response.status_code}")
            continue
        
        content = response.text
        print(f"Content of {module_url}:\n{content[:200]}")  # 输出前200个字符进行调试

        # 提取不同部分
        module_rules = extract_section(content, "Rule")
        if module_rules:
            rules += [f"# {module_url.split('/')[-1].split('.')[0]}"] + module_rules
            print(f"Extracted {len(module_rules)} rules from {module_url}")  # 调试信息
        else:
            print(f"No rules found in {module_url}")  # 调试信息

        rewrites += extract_section(content, "Rewrite")
        scripts += extract_section(content, "Script")
        mitm_section = extract_section(content, "MITM")

        if mitm_section:
            mitm_hosts.append(mitm_section[0].replace("Hostname =", "").strip())

    combined_mitmh = "Hostname = %APPEND% " + ", ".join(mitm_hosts)

    output_file_name = os.path.splitext(os.path.basename(input_file))[0].replace("Modules-", "") + ".sgmodule"
    name = output_file_name.replace(".sgmodule", "").capitalize()  # 获取名称

    output_path = f"Modules/Surge/{output_file_name}"

    # 创建目录如果不存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as output_file:
        output_file.write(f"# !name= 🧰 {name}\n")
        output_file.write("# !desc= Tools for Surge & Shadowrocket\n")
        output_file.write("# !category=Jacob\n\n")

        output_file.write("[Rule]\n")
        output_file.write("\n".join(rules) + "\n\n")

        output_file.write("[Rewrite]\n")
        output_file.write("\n".join(rewrites) + "\n\n")

        output_file.write("[Script]\n")
        output_file.write("\n".join(scripts) + "\n\n")

        output_file.write("[MITM]\n")
        output_file.write(combined_mitmh + "\n")

    print(f"合并完成！生成的文件为 {output_path}")

def download_modules(module_file):
    with open(module_file, 'r') as f:
        module_urls = f.read().splitlines()

    for url in module_urls:
        response = requests.get(url)
        if response.status_code == 200:
            filename = url.split('/')[-1]
            with open(filename, 'wb') as module_file:
                module_file.write(response.content)
            print(f"下载完成：{filename}")
        else:
            print(f"下载失败：{url}")

# 示例使用
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("请提供要处理的模块文件路径")
        sys.exit(1)

    for module_file in sys.argv[1:]:
        download_modules(module_file)
        merge_modules(module_file)
