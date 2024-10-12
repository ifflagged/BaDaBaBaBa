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

def merge_modules(input_file, is_loon=False):
    with open(input_file, 'r') as f:
        module_urls = f.read().splitlines()

    rules = []
    rewrites = []
    scripts = []
    mitm_hosts = set()

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

        # 提取 Hostname 部分
        mitm_section = extract_section(content, "MITM")
        if mitm_section:
            for line in mitm_section:
                if line.startswith("Hostname ="):
                    hosts = line.split("=", 1)[1].strip()
                    mitm_hosts.update(host.strip() for host in hosts.split(",") if host.strip())

    # 根据插件类型生成输出文件名和内容
    if is_loon:
        output_file_name = os.path.splitext(os.path.basename(input_file))[0].replace("Modules-", "") + ".plugin"
        name = output_file_name.replace(".plugin", "").capitalize()
        header = f"# !name= {name}\n# !desc = Merger {name} for Loon\n# !author = Jacob[https://github.com/ifflagged/BaDaBaBaBa]\n# !icon = https://github.com/Semporia/Hand-Painted-icon/raw/master/Universal/Reject.orig.png\n\n"
    else:
        output_file_name = os.path.splitext(os.path.basename(input_file))[0].replace("Modules-", "") + ".sgmodule"
        name = output_file_name.replace(".sgmodule", "").capitalize()
        header = f"# !name= 🧰 {name}\n# !desc= Merger {name} for Surge & Shadowrocket\n# !category=Jacob\n\n"

    output_path = f"Modules/Surge/{output_file_name}"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as output_file:
        output_file.write(header)

        output_file.write("[Rule]\n")
        output_file.write("\n".join(rules) + "\n\n")

        output_file.write("[Rewrite]\n")
        output_file.write("\n".join(rewrites) + "\n\n")

        output_file.write("[Script]\n")
        output_file.write("\n".join(scripts) + "\n\n")

        if is_loon:
            # 对于 Loon，不加 %APPEND%
            combined_mitmh = ", ".join(sorted(mitm_hosts)) if mitm_hosts else ""
            output_file.write("[MITM]\n")
            output_file.write(combined_mitmh + "\n")
        else:
            combined_mitmh = "Hostname = %APPEND% " + ", ".join(sorted(mitm_hosts))
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
        if module_file.endswith('.sgmodule'):
            download_modules(module_file)
            merge_modules(module_file, is_loon=False)
        elif module_file.endswith('.plugin'):
            download_modules(module_file)
            merge_modules(module_file, is_loon=True)
