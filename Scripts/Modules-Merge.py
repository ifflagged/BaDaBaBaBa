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
        elif in_section and (not line.startswith("#")): # 要保留原来的#则修改为 elif in_section and (not line.startswith("#")):
            stripped_line = line.strip()
            if stripped_line:
                section_lines.append(stripped_line)

    return section_lines

def extract_arguments_and_select(content):
    arguments, arguments_desc, selects = [], [], []
    for line in content.splitlines():
        if line.startswith("#!arguments="):
            arguments.append(line.replace("#!arguments=", "").strip())
        elif line.startswith("#!arguments-desc="):
            arguments_desc.append(line.replace("#!arguments-desc=", "").strip())
        elif line.startswith("#!select"):
            selects.append(line.strip())
    return arguments, arguments_desc, selects

def merge_modules(input_file, output_type, module_urls):
    # Initialize module_content
    module_content = {
        "Argument": [],
        "General": [],
        "Rule": [],
        "Rewrite": [],
        "URL Rewrite": [],
        "Header Rewrite": [],
        "Host": [],
        "Map Local": [],
        "SSID Setting": [],
        "Script": [],
        "MITM": set(),
    }

    added_sets = {section: set() for section in module_content if section != "MITM"}

    for module_url in module_urls:
        response = requests.get(module_url)
        if response.status_code != 200:
            continue

        content = response.text

        # Extract various sections
        sections = ["Argument", "General", "Rule", "Header Rewrite", "Host", "Map Local", "SSID Setting", "Script"]
        
        for section in sections:
            section_content = extract_section(content, section)
            if section_content:
                module_content[section].append(f"# {module_url.split('/')[-1].split('.')[0]}")
                for line in section_content:
                    if line not in added_sets[section]:
                        added_sets[section].add(line)
                        module_content[section].append(line)

        # Extract Rewrite and URL Rewrite sections
        module_rewrites = extract_section(content, "Rewrite")
        module_url_rewrites = extract_section(content, "URL Rewrite")

        if output_type == 'sgmodule':
            if module_rewrites or module_url_rewrites:
                module_content["URL Rewrite"].append(f"# {module_url.split('/')[-1].split('.')[0]}")
                for line in module_rewrites + module_url_rewrites:
                    if line not in added_sets["Rewrite"]:
                        added_sets["Rewrite"].add(line)
                        module_content["URL Rewrite"].append(line)
        else:
            if module_rewrites:
                module_content["Rewrite"].append(f"# {module_url.split('/')[-1].split('.')[0]}")
                for line in module_rewrites:
                    if line not in added_sets["Rewrite"]:
                        added_sets["Rewrite"].add(line)
                        module_content["Rewrite"].append(line)

        # Extract MITM section
        mitm_section = extract_section(content, "MITM")
        if mitm_section:
            append_hosts = set()
            disabled_hosts = set()
    
            for line in mitm_section:
                if line.lower().startswith("hostname = %append%"):
                    hosts = line.lower().replace("hostname = %append%", "").strip()
                    append_hosts.update(host.strip() for host in hosts.split(",") if host.strip())
                elif line.lower().startswith("hostname = %insert%"):
                    hosts = line.lower().replace("hostname = %insert%", "").strip()
                    append_hosts.update(host.strip() for host in hosts.split(",") if host.strip())
                elif line.lower().startswith("hostname-disabled = %insert%"):
                    disabled_hosts = set(line.lower().replace("hostname-disabled = %insert%", "").strip().split(","))
    
            if append_hosts:
                module_content["MITM"].add(f"hostname = %APPEND%, " + ", ".join(sorted(append_hosts)))
            if disabled_hosts:
                module_content["MITM"].add(f"hostname-disabled = %INSERT%, " + ", ".join(sorted(disabled_hosts)))

            else:
                for line in mitm_section:
                    if line.lower().startswith("hostname ="):
                        hosts = line.lower().replace("hostname =", "").strip()
                        module_content["MITM"].update(host.strip() for host in hosts.split(",") if host.strip())
                    else:
                        module_content["MITM"].update(line.strip().split(","))
                        
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

            # Extract Arguments and Descriptions
            all_arguments, all_arguments_desc = [], []
            for module_url in module_urls:
                response = requests.get(module_url)
                if response.status_code == 200:
                    content = response.text
                    arguments, arguments_desc, _ = extract_arguments_and_select(content)
                    all_arguments.extend(arguments)

                    # Format arguments-desc
                    if arguments_desc:
                        module_name = f"# {module_url.split('/')[-1].split('.')[0]}"
                        # Format the description to include literal \n
                        formatted_desc = f"{module_name}\\n" + "\\n".join(arguments_desc)
                        all_arguments_desc.append(formatted_desc)

            if all_arguments:
                output_file.write(f"#!arguments= " + ", ".join(all_arguments) + "\n")

            if all_arguments_desc:
                # Join formatted descriptions with double newline, but ensure no trailing newline at the end
                output_file.write(f"#!arguments-desc= " + "\\n\\n".join(all_arguments_desc) + "\n\n")
            else:
                output_file.write("\n")

        else:  # for plugin
            output_file.write(f"#!name= Merged {name}\n")
            output_file.write(f"#!desc= Merger {name} for Loon\n")
            output_file.write("#!author= Jacob[https://github.com/ifflagged/BaDaBaBaBa]\n")
            output_file.write("#!icon= https://github.com/Semporia/Hand-Painted-icon/raw/master/Universal/Reject.orig.png\n")

            # Extract selects
            all_selects = []
            added_selects = set()  # Track already added selects
            for module_url in module_urls:
                response = requests.get(module_url)
                if response.status_code == 200:
                    content = response.text
                    _, _, selects = extract_arguments_and_select(content)
                    if selects:
                        # Add the reference comment only once before selects from this URL
                        reference_comment = f"# {module_url.split('/')[-1].split('.')[0]}"
                        if any(select not in added_selects for select in selects):
                            all_selects.append(reference_comment)

                        for select in selects:
                            if select not in added_selects:
                                all_selects.append(select)
                                added_selects.add(select)  # Add select to the set

            if all_selects:
                output_file.write("\n".join(all_selects) + "\n\n")
            else:
                output_file.write("\n")

        # Write each section, deduplicated
        for section_name, content_list in module_content.items():
            if content_list and any(line.strip() for line in content_list):
                output_file.write(f"[{section_name}]\n")
                if section_name == "MITM":
                    combined_mitmh = "hostname = %APPEND%, " + ", ".join(sorted(module_content["MITM"])) if module_content["MITM"] else ""
                    output_file.write(combined_mitmh + "\n")
                    if module_content["MITM"]:
                        disabled_hosts = "hostname-disabled = %INSERT%, " + ", ".join(sorted(module_content["MITM"]))
                        output_file.write(disabled_hosts + "\n")
                else:
                    output_file.write("\n".join(content_list) + "\n")
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
