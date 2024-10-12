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

def merge_modules(input_file, output_type, module_urls):
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

        # 提取 Hostname 部分
        mitm_section = extract_section(content, "MITM")
        if mitm_section:
            if output_type == 'sgmodule':
                for line in mitm_section:
                    if line.startswith("Hostname = %APPEND%"):
                        hosts = line.replace("Hostname = %APPEND%", "").strip()
                        mitm_hosts.update(host.strip() for host in hosts.split(",") if host.strip())
            else:  # 对于 .plugin 文件
                for line in mitm_section:
                    mitm_hosts.update(line.strip().split(","))

    # 生成 Hostname 字符串
    if output_type == 'sgmodule':
        combined_mitmh = "Hostname = %APPEND% " + ", ".join(sorted(mitm_hosts))
    else:
        combined_mitmh = ", ".join(sorted(mitm_hosts))  # 直接合并，不加 %APPEND%

    name = os.path.splitext(os.path.basename(input_file))[0].replace("Modules-", "").capitalize()
    output_file_name = f"{name}.{'sgmodule' if output_type == 'sgmodule' else 'plugin'}"
    output_path = f"Modules/{'Surge' if output_type == 'sgmodule' else 'Loon'}/{output_file_name}"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as output_file:
        if output_type == 'sgmodule':
            output_file.write(f"# !name= 🧰 {name}\n")
            output_file.write(f"# !desc= Merger {name} for Surge & Shadowrocket\n")
            output_file.write("# !category=Jacob\n\n")
        else:
            output_file.write(f"#!name= {name}\n")
            output_file.write(f"#!desc= Merger {name} for Loon\n")
            output_file.write("#!author= Jacob[https://github.com/ifflagged/BaDaBaBaBa]\n")
            output_file.write("#!icon= https://github.com/Semporia/Hand-Painted-icon/raw/master/Universal/Reject.orig.png\n\n")

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

    surge_urls = []
    loon_urls = []

    for url in module_urls:
        if ".sgmodule" in url:
            surge_urls.append(url)
        elif ".plugin" in url:
            loon_urls.append(url)

    if surge_urls:
        merge_modules(module_file, 'sgmodule', surge_urls)
    if loon_urls:
        merge_modules(module_file, 'plugin', loon_urls)

# 示例使用
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("请提供要处理的模块文件路径")
        sys.exit(1)

    for module_file in sys.argv[1:]:
        download_modules(module_file)
