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
        elif in_section:
            stripped_line = line.strip()
            if stripped_line:  # 过滤掉空行和仅有空格的行
                section_lines.append(stripped_line)
    
    return section_lines

def extract_arguments(content):
    arguments = []
    arguments_desc = []
    for line in content.splitlines():
        if line.startswith("#!arguments="):
            arguments.append(line.replace("#!arguments=", "").strip())
        elif line.startswith("#!arguments-desc="):
            arguments_desc.append(line.replace("#!arguments-desc=", "").strip())
    return arguments, arguments_desc

def extract_select(content):
    selects = []
    for line in content.splitlines():
        if line.startswith("#!select"):
            selects.append(line.strip())
    return selects

def merge_modules(input_file, output_type, module_urls):
    general = []
    rules = []
    rewrites = []
    scripts = []
    mitm_hosts = set()

    # 定义一个字典来存储各部分的内容，每个部分按模块顺序保存
    module_content = {
        "General": [],
        "Rule": [],
        "Rewrite": [],
        "Script": [],
        "MITM": set(),
        "Arguments": [],
        "ArgumentsDesc": [],
        "Select": []
    }

    # 添加用于去重的集合
    added_general = set()
    added_rules = set()
    added_rewrites = set()
    added_scripts = set()

    for module_url in module_urls:
        response = requests.get(module_url)

        if response.status_code != 200:
            continue

        content = response.text

        # 提取 General
        module_general = extract_section(content, "General")
        if module_general:
            module_content["General"].append(f"# {module_url.split('/')[-1].split('.')[0]}")
            for line in module_general:
                if line not in added_general:
                    added_general.add(line)  # 添加到已添加集合中
                    module_content["General"].append(line)

        # 提取 Rule
        module_rules = extract_section(content, "Rule")
        if module_rules:
            module_content["Rule"].append(f"# {module_url.split('/')[-1].split('.')[0]}")
            for line in module_rules:
                if line not in added_rules:
                    added_rules.add(line)
                    module_content["Rule"].append(line)

        # 提取 Rewrite
        module_rewrites = extract_section(content, "Rewrite")
        module_url_rewrites = extract_section(content, "URL Rewrite")
        if module_rewrites or module_url_rewrites:
            module_content["Rewrite"].append(f"# {module_url.split('/')[-1].split('.')[0]}")
            for line in module_rewrites:
                if line not in added_rewrites:
                    added_rewrites.add(line)
                    module_content["Rewrite"].append(line)
            for line in module_url_rewrites:
                if line not in added_rewrites:
                    added_rewrites.add(line)
                    module_content["Rewrite"].append(line)

        # 提取 Script
        module_scripts = extract_section(content, "Script")
        if module_scripts:
            module_content["Script"].append(f"# {module_url.split('/')[-1].split('.')[0]}")
            for line in module_scripts:
                if line not in added_scripts:
                    added_scripts.add(line)
                    module_content["Script"].append(line)

        # 提取 MITM
        mitm_section = extract_section(content, "MITM")
        if mitm_section:
            if output_type == 'sgmodule':
                for line in mitm_section:
                    if line.lower().startswith("hostname = %append%"):
                        hosts = line.lower().replace("hostname = %append%", "").strip()
                        module_content["MITM"].update(host.strip() for host in hosts.split(",") if host.strip())
            else:
                for line in mitm_section:
                    if line.lower().startswith("hostname ="):
                        hosts = line.lower().replace("hostname =", "").strip()
                        module_content["MITM"].update(host.strip() for host in hosts.split(",") if host.strip())
                    else:
                        module_content["MITM"].update(line.strip().split(","))

        # 提取 arguments 和 select 内容
        arguments, arguments_desc = extract_arguments(content)
        if output_type == 'sgmodule':
            module_content["Arguments"].extend(arguments)
            for desc in arguments_desc:
                # 将 '\n' 保留为文本而不是换行
                desc_with_newline = desc.replace("\n", r"\n")
                module_content["ArgumentsDesc"].append(f"# {module_url.split('/')[-1].split('.')[0]}\\n{desc_with_newline}")
        else:
            selects = extract_select(content)
            if selects:
                # 确保只插入一次 URL 注释
                module_content["Select"].append(f"# {module_url.split('/')[-1].split('.')[0]}")
                module_content["Select"].extend(selects)

    # 去重并保持每个模块下内容的顺序
    if output_type == 'sgmodule':
        combined_mitmh = "hostname = %APPEND% " + ", ".join(sorted(module_content["MITM"])) if module_content["MITM"] else ""
    else:
        combined_mitmh = "hostname = " + ", ".join(sorted(module_content["MITM"])) if module_content["MITM"] else ""

    name = os.path.splitext(os.path.basename(input_file))[0].replace("Merge-Modules-", "").capitalize()
    output_file_name = f"{name}.{'sgmodule' if output_type == 'sgmodule' else 'plugin'}"
    output_path = f"Modules/{'Surge' if output_type == 'sgmodule' else 'Loon'}/{output_file_name}"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 写入合并结果
    with open(output_path, "w") as output_file:
        if output_type == 'sgmodule':
            output_file.write(f"#!name= 🧰 Merged {name}\n")
            output_file.write(f"#!desc= Merger {name} for Surge & Shadowrocket\n")
            output_file.write("#!category= Jacob\n")

            if module_content["Arguments"]:
                arguments_line = f"#!arguments= " + ", ".join(module_content["Arguments"])
                output_file.write(arguments_line + "\n")
            
            if module_content["ArgumentsDesc"]:
                arguments_desc_line = " ".join(module_content["ArgumentsDesc"])
                output_file.write(f"#!arguments-desc= {arguments_desc_line}\n\n")  # 空一行
            else:
                output_file.write("\n")  # 如果没有ArgumentsDesc，仍然空一行

        else:
            output_file.write(f"#!name= Merged {name}\n")
            output_file.write(f"#!desc= Merger {name} for Loon\n")
            output_file.write("#!author= Jacob[https://github.com/ifflagged/BaDaBaBaBa]\n")
            output_file.write("#!icon= https://github.com/Semporia/Hand-Painted-icon/raw/master/Universal/Reject.orig.png\n")

            if module_content["Select"]:
                output_file.write("\n".join(module_content["Select"]) + "\n\n")  # 如果有select部分，输出并空一行
            else:
                output_file.write("\n")  # 如果没有select部分，仍然空一行

        # 逐一写入各部分内容，并按模块顺序保持去重后的内容在注释下面
        for section_name, content_list in module_content.items():
            if content_list and any(line.strip() for line in content_list):
                if section_name == "MITM":
                    output_file.write("[MITM]\n")
                    output_file.write(combined_mitmh + "\n")
                    break  # 结束写入，跳过后续的内容
                else:
                    output_file.write(f"[{section_name}]\n")
                    output_file.write("\n".join(content_list) + "\n\n")

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
