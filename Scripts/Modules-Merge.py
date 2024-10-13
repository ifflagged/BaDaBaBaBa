import requests
import os
import sys

def extract_section(content, section_name):
    lines = content.splitlines()
    in_section = False
    section_lines = []
    section_name_lower = section_name.lower()

    for line in lines:
        line_lower = line.lower()
        if line_lower.startswith(f"[{section_name_lower}]"):
            in_section = True
        elif line_lower.startswith("[") and in_section:
            break
        elif in_section and (not line.startswith("#")):
            stripped_line = line.strip()
            if stripped_line:  # 过滤掉空行和仅有空格的行
                section_lines.append(stripped_line)
    
    return section_lines

def merge_modules(input_file, output_type, module_urls):
    general = set()  # 使用 set 去重
    rules = set()
    rewrites = set()
    scripts = set()
    mitm_hosts = set()

    for module_url in module_urls:
        response = requests.get(module_url)
        
        if response.status_code != 200:
            continue
        
        content = response.text

        module_general = extract_section(content, "General")
        if module_general:
            general.update([f"# {module_url.split('/')[-1].split('.')[0]}"] + module_general)

        module_rules = extract_section(content, "Rule")
        if module_rules:
            rules.update([f"# {module_url.split('/')[-1].split('.')[0]}"] + module_rules)

        # 提取 [Rewrite] 和 [URL Rewrite]，并将其合并到 Surge 的 [URL Rewrite] 部分
        if output_type == 'sgmodule':
            module_rewrites = extract_section(content, "Rewrite")
            module_url_rewrites = extract_section(content, "URL Rewrite")
            if module_rewrites:
                rewrites.update([f"# {module_url.split('/')[-1].split('.')[0]}"] + module_rewrites)
            if module_url_rewrites:
                rewrites.update([f"# {module_url.split('/')[-1].split('.')[0]}"] + module_url_rewrites)
        else:
            # 对于 Loon，保留 [Rewrite]
            module_rewrites = extract_section(content, "Rewrite")
            if module_rewrites:
                rewrites.update([f"# {module_url.split('/')[-1].split('.')[0]}"] + module_rewrites)

        module_scripts = extract_section(content, "Script")
        if module_scripts:
            scripts.update([f"# {module_url.split('/')[-1].split('.')[0]}"] + module_scripts)

        mitm_section = extract_section(content, "MITM")
        if mitm_section:
            if output_type == 'sgmodule':
                for line in mitm_section:
                    if line.lower().startswith("hostname = %append%"):
                        hosts = line.lower().replace("hostname = %append%", "").strip()
                        mitm_hosts.update(host.strip() for host in hosts.split(",") if host.strip())
            else:
                for line in mitm_section:
                    if line.lower().startswith("hostname ="):
                        hosts = line.lower().replace("hostname =", "").strip()
                        mitm_hosts.update(host.strip() for host in hosts.split(",") if host.strip())
                    else:
                        mitm_hosts.update(line.strip().split(","))

    if output_type == 'sgmodule':
        combined_mitmh = "hostname = %APPEND% " + ", ".join(sorted(mitm_hosts)) if mitm_hosts else ""
    else:
        combined_mitmh = "hostname = " + ", ".join(sorted(mitm_hosts)) if mitm_hosts else ""

    name = os.path.splitext(os.path.basename(input_file))[0].replace("Merge-Modules-", "").capitalize()
    output_file_name = f"{name}.{'sgmodule' if output_type == 'sgmodule' else 'plugin'}"
    output_path = f"Modules/{'Surge' if output_type == 'sgmodule' else 'Loon'}/{output_file_name}"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as output_file:
        if output_type == 'sgmodule':
            output_file.write(f"#!name= 🧰 Merged {name}\n")
            output_file.write(f"#!desc= Merger {name} for Surge & Shadowrocket\n")
            output_file.write("#!category=Jacob\n\n")
        else:
            output_file.write(f"#!name= Merged {name}\n")
            output_file.write(f"#!desc= Merger {name} for Loon\n")
            output_file.write("#!author= Jacob[https://github.com/ifflagged/BaDaBaBaBa]\n")
            output_file.write("#!icon= https://github.com/Semporia/Hand-Painted-icon/raw/master/Universal/Reject.orig.png\n\n")

        # General 部分
        if general:
            output_file.write("[General]\n")
            output_file.write("\n".join(sorted(general)) + "\n\n")

        # Rule 部分
        if rules:
            output_file.write("[Rule]\n")
            output_file.write("\n".join(sorted(rules)) + "\n\n")

        # 将 [Rewrite] 和 [URL Rewrite] 合并到 [URL Rewrite]，且不再在注释中标注类型
        if rewrites:
            output_file.write("[URL Rewrite]\n" if output_type == 'sgmodule' else "[Rewrite]\n")
            output_file.write("\n".join(sorted(rewrites)) + "\n\n")

        # Script 部分
        if scripts:
            output_file.write("[Script]\n")
            output_file.write("\n".join(sorted(scripts)) + "\n\n")

        # MITM 部分
        if mitm_hosts:
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
