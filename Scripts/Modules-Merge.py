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
            if stripped_line:
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
    module_content = {
        "General": set(),
        "Rule": set(),
        "Rewrite": set(),
        "URL Rewrite": set(),
        "Header Rewrite": set(),
        "Host": set(),
        "Map Local": set(),
        "SSID Setting": set(),
        "Script": set(),
        "MITM": set(),
        "Arguments": [],
        "ArgumentsDesc": [],
        "Select": []
    }

    for module_url in module_urls:
        try:
            response = requests.get(module_url)
            response.raise_for_status()
            content = response.text

            # Extract various sections
            sections = ["General", "Rule", "Header Rewrite", "Host", "Map Local", "SSID Setting", "Script"]
            for section in sections:
                section_content = extract_section(content, section)
                if section_content:
                    module_content[section].update(section_content)

            # Extract Rewrite sections
            if output_type == 'sgmodule':
                module_content["URL Rewrite"].update(extract_section(content, "Rewrite"))
                module_content["URL Rewrite"].update(extract_section(content, "URL Rewrite"))
            else:
                module_content["Rewrite"].update(extract_section(content, "Rewrite"))

            # Extract MITM section
            mitm_section = extract_section(content, "MITM")
            if mitm_section:
                module_content["MITM"].update(line.strip() for line in mitm_section)

            # Extract Arguments and Select sections
            arguments, arguments_desc = extract_arguments(content)
            module_content["Arguments"].extend(arguments)
            module_content["ArgumentsDesc"].extend(arguments_desc)

            selects = extract_select(content)
            if selects:
                module_content["Select"].append(f"# {module_url.split('/')[-1].split('.')[0]}")
                module_content["Select"].extend(selects)

        except requests.RequestException as e:
            print(f"Error fetching {module_url}: {e}")

    # Construct output file path
    name = os.path.splitext(os.path.basename(input_file))[0].replace("Merge-Modules-", "").capitalize()
    output_file_name = f"{name}.{'sgmodule' if output_type == 'sgmodule' else 'plugin'}"
    output_path = f"Modules/{'Surge' if output_type == 'sgmodule' else 'Loon'}/{output_file_name}"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write merged content to file
    with open(output_path, "w") as output_file:
        if output_type == 'sgmodule':
            output_file.write(f"#!name= 🧰 Merged {name}\n")
            output_file.write(f"#!desc= Merger {name} for Surge & Shadowrocket\n")
            output_file.write("#!category= Jacob\n")
            output_file.write(f"# Arguments: {', '.join(module_content['Arguments'])}\n")
            output_file.write(f"# Arguments Desc: {' '.join(module_content['ArgumentsDesc'])}\n\n")
        else:
            output_file.write(f"#!name= Merged {name}\n")
            output_file.write(f"#!desc= Merger {name} for Loon\n")
            output_file.write("#!author= Jacob[https://github.com/ifflagged/BaDaBaBaBa]\n")
            output_file.write("#!icon= https://github.com/Semporia/Hand-Painted-icon/raw/master/Universal/Reject.orig.png\n")
            if module_content["Select"]:
                output_file.write("\n".join(module_content["Select"]) + "\n\n")
            if module_content["Arguments"]:
                output_file.write("[Argument]\n")
                output_file.write("\n".join(module_content["Arguments"]) + "\n\n")

        # Write each section, deduplicated
        for section_name, content_set in module_content.items():
            if content_set and any(line.strip() for line in content_set):
                output_file.write(f"[{section_name}]\n")
                if section_name == "MITM":
                    output_file.write("hostname = " + ", ".join(sorted(module_content["MITM"])) + "\n")
                else:
                    output_file.write("\n".join(sorted(content_set)) + "\n")
                output_file.write("\n")

    print(f"Merged content written to {output_path}")

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
