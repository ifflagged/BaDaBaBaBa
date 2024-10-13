import requests
import os
import sys

def extract_arguments(content):
    args = []
    args_desc = []
    lines = content.splitlines()
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith("#!arguments="):
            args.append(stripped_line.replace("#!arguments=", "").strip())
        elif stripped_line.startswith("#!arguments-desc="):
            args_desc.append(f"# {stripped_line.replace('#!arguments-desc=', '').strip()}\n")
    return ", ".join(args), "".join(args_desc)

def extract_select(content):
    select_lines = []
    lines = content.splitlines()
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith("#!select =") or stripped_line.startswith("#!select="):
            select_lines.append(f"# {stripped_line}\n")
    return "".join(select_lines)

def merge_modules(input_file, output_type, module_urls):
    general = []
    rules = []
    rewrites = []
    scripts = []
    mitm_hosts = set()
    arguments = []
    arguments_desc = []
    selects = []

    module_content = {
        "General": [],
        "Rule": [],
        "Rewrite": [],
        "Script": [],
        "MITM": set()
    }

    for module_url in module_urls:
        response = requests.get(module_url)
        if response.status_code != 200:
            continue

        content = response.text

        # Extract each section
        module_general = extract_section(content, "General")
        if module_general:
            module_content["General"].append(f"# {module_url.split('/')[-1].split('.')[0]}")
            module_content["General"].extend(module_general)

        module_rules = extract_section(content, "Rule")
        if module_rules:
            module_content["Rule"].append(f"# {module_url.split('/')[-1].split('.')[0]}")
            module_content["Rule"].extend(module_rules)

        module_rewrites = extract_section(content, "Rewrite")
        module_url_rewrites = extract_section(content, "URL Rewrite")
        if module_rewrites or module_url_rewrites:
            module_content["Rewrite"].append(f"# {module_url.split('/')[-1].split('.')[0]}")
            if module_rewrites:
                module_content["Rewrite"].extend(module_rewrites)
            if module_url_rewrites:
                module_content["Rewrite"].extend(module_url_rewrites)

        module_scripts = extract_section(content, "Script")
        if module_scripts:
            module_content["Script"].append(f"# {module_url.split('/')[-1].split('.')[0]}")
            module_content["Script"].extend(module_scripts)

        mitm_section = extract_section(content, "MITM")
        if mitm_section:
            for line in mitm_section:
                if line.lower().startswith("hostname = %append%"):
                    hosts = line.lower().replace("hostname = %append%", "").strip()
                    module_content["MITM"].update(host.strip() for host in hosts.split(",") if host.strip())
                else:
                    hosts = line.lower().replace("hostname =", "").strip()
                    module_content["MITM"].update(host.strip() for host in hosts.split(",") if host.strip())

        # Extract arguments and select based on type
        if output_type == 'sgmodule':
            args, args_desc = extract_arguments(content)
            if args:
                arguments.append(args)
            if args_desc:
                arguments_desc.append(args_desc)
        elif output_type == 'plugin':
            select_lines = extract_select(content)
            if select_lines:
                selects.append(select_lines)

    # Combine MITM hosts
    if output_type == 'sgmodule':
        combined_mitmh = "hostname = %APPEND% " + ", ".join(sorted(module_content["MITM"])) if module_content["MITM"] else ""
    else:
        combined_mitmh = "hostname = " + ", ".join(sorted(module_content["MITM"])) if module_content["MITM"] else ""

    # Output file creation
    name = os.path.splitext(os.path.basename(input_file))[0].replace("Merge-Modules-", "").capitalize()
    output_file_name = f"{name}.{'sgmodule' if output_type == 'sgmodule' else 'plugin'}"
    output_path = f"Modules/{'Surge' if output_type == 'sgmodule' else 'Loon'}/{output_file_name}"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write merged content
    with open(output_path, "w") as output_file:
        if output_type == 'sgmodule':
            output_file.write(f"#!name= 🧰 Merged {name}\n")
            output_file.write(f"#!desc= Merger {name} for Surge & Shadowrocket\n")
            output_file.write("#!category=Jacob\n")
            if arguments:
                output_file.write(f"#!arguments= {', '.join(arguments)}\n")
            if arguments_desc:
                output_file.write(f"#!arguments-desc=\n{''.join(arguments_desc)}\n")
        else:
            output_file.write(f"#!name= Merged {name}\n")
            output_file.write(f"#!desc= Merger {name} for Loon\n")
            output_file.write("#!author= Jacob[https://github.com/ifflagged/BaDaBaBaBa]\n")
            output_file.write("#!icon= https://github.com/Semporia/Hand-Painted-icon/raw/master/Universal/Reject.orig.png\n")
            if selects:
                output_file.write(f"{''.join(selects)}")

        # Write sections
        for section_name, content_list in module_content.items():
            if content_list and any(line.strip() for line in content_list):
                if section_name == "MITM":
                    output_file.write("[MITM]\n")
                    output_file.write(combined_mitmh + "\n")
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
