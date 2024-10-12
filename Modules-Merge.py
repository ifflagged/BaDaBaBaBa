import requests
import os
import sys

def extract_section(content, section_name):
    lines = content.splitlines()
    in_section = False
    section_lines = []

    for line in lines:
        if line.startswith(f"[{section_name}]"):
            in_section = True
        elif line.startswith("[") and in_section:
            break
        elif in_section and (not line.startswith("#")):  # 忽略注释行
            section_lines.append(line.strip())
    
    return section_lines

def merge_modules(input_file):
    with open(input_file, 'r') as f:
        module_urls = f.read().splitlines()

    rules = []
    rewrites = []
    scripts = []
    mitm_hosts = set()  # 使用集合来去重

    for module_url in module_urls:
        response = requests.get(module_url)
        
        if response.status_code != 200:
            continue
        
        content = response.text

        # 提取不同部分
        module_rules = extract_section(content, "Rule")
        if module_rules:
            rules += [f"# {module_url.split('/')[-1].split('.')[0]}"] + module_rules

        module_rewrites = extract_section(content, "Rewrite")
        if module_rewrites:
            rewrites += [f"# {module_url.split('/')[-1].split('.')[0]}"] + module_rewrites

        module_scripts = extract_section(content, "Script")
        if module_scripts:
            scripts += [f"# {module_url.split('/')[-1].split('.')[0]}"] + module_scripts

        mitm_section = extract_section(content, "MITM")
        if mitm_section:
            mitm_hosts.add(mitm_section[0].replace("Hostname =", "").strip())

    combined_mitmh = "Hostname = %APPEND% " + ", ".join(sorted(mitm_hosts))

    output_file_name = os.path.splitext(os.path.basename(input_file))[0].replace("Modules-", "") + ".sgmodule"
    name = output_file_name.replace(".sgmodule", "").capitalize()

    output_path = f"Modules/Surge/{output_file_name}"

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

# 示例使用
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("请提供要处理的模块文件路径")
        sys.exit(1)

    for module_file in sys.argv[1:]:
        download_modules(module_file)
        merge_modules(module_file)
