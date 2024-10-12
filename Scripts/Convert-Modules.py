import os
import sys
import re
import requests

def get_unique_filename(base_path):
    """Generate a unique filename by appending a number if the file exists."""
    count = 1
    while os.path.exists(base_path):
        base_path = f"{base_path.rsplit('.', 1)[0]}-{count}.{base_path.rsplit('.', 1)[1]}"
        count += 1
    return base_path

def convert_file(input_file, module_name, comment):
    # Common replacements for both Surge and Loon
    sed_common = [
        (r'/raw.githubusercontent.com/ s/\/main\//\/raw\/main\//Ig', ''),
        (r'/raw.githubusercontent.com/ s/\/master\//\/raw\/master\//Ig', ''),
        (r's/raw.githubusercontent.com/github.com/Ig', ''),
        (r's/HOST,/DOMAIN,/Ig', ''),
        (r's/HOST-SUFFIX,/DOMAIN-SUFFIX,/Ig', ''),
        (r's/HOST-KEYWORD,/DOMAIN-KEYWORD,/Ig', ''),
        (r's/IP-CIDR,/IP-CIDR,/Ig', ''),
        (r's/IP6-CIDR,/IP-CIDR6,/Ig', ''),
        (r'/IP-CIDR/ s/\(REJECT\)\([^,]*$\)/\1, no-resolve/Ig', ''),
    ]

    surge_output_file = f"Modules/Surge/{module_name}.sgmodule"
    surge_output_file = get_unique_filename(surge_output_file)

    loon_output_file = f"Modules/Loon/{module_name}.plugin"
    loon_output_file = get_unique_filename(loon_output_file)

    # Surge conversion
    with open(input_file, 'r') as infile, open(surge_output_file, 'w') as outfile:
        outfile.write(f"{comment}\n")
        for line in infile:
            for pattern, replacement in sed_common:
                line = re.sub(pattern, replacement, line)
            # Additional replacements specific to Surge...
            outfile.write(line)

    # Loon conversion
    with open(input_file, 'r') as infile, open(loon_output_file, 'w') as outfile:
        outfile.write(f"{comment}\n")
        for line in infile:
            for pattern, replacement in sed_common:
                line = re.sub(pattern, replacement, line)
            # Additional replacements specific to Loon...
            outfile.write(line)

if __name__ == "__main__":
    input_file = sys.argv[1]
    module_name = sys.argv[2]
    comment = sys.argv[3]
    convert_file(input_file, module_name, comment)
