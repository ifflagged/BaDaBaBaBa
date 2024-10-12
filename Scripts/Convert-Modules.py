import sys
import re
import os

def apply_replacements(content, replacements):
    for pattern, repl in replacements:
        content = [re.sub(pattern, repl, line, flags=re.IGNORECASE) for line in content]
    return content

def process_file(input_file, module_name, comment, output_dir, is_surge=True):
    with open(input_file, 'r') as file:
        content = file.readlines()

    # Common replacements
    common_replacements = [
        (r'raw\.githubusercontent\.com/(main|master)/', r'raw/\1/'),
        (r'raw\.githubusercontent\.com/github\.com', 'github.com'),
        (r'HOST,', 'DOMAIN,'),
        (r'HOST-SUFFIX,', 'DOMAIN-SUFFIX,'),
        (r'HOST-KEYWORD,', 'DOMAIN-KEYWORD,'),
        (r'IP-CIDR,', 'IP-CIDR,'),
        (r'IP6-CIDR,', 'IP-CIDR6,'),
        (r'(\bREJECT\b)([^,]*)$', r'\1, no-resolve'),
    ]

    content = apply_replacements(content, common_replacements)

    replacements = {
        'surge': [
            (r'url reject-200', r'- reject'),
            (r'url reject-img', r'- reject'),
            (r'url reject-dict', r'- reject'),
            (r'url reject-array', r'- reject'),
            (r'url reject-video', r'- reject'),
            (r'url reject-replace', r'- reject'),
            (r'url reject', r'- reject'),
            (r'url script-response-body', f'{module_name} = type=http-response,pattern='),
            (r'url script-echo-response', f'{module_name} = type=http-response,pattern='),
            (r'url script-response-header', f'{module_name} = type=http-response,pattern='),
            (r'url script-request-body', f'{module_name} = type=http-request,pattern='),
            (r'url script-request-header', f'{module_name} = type=http-request,pattern='),
            (r'url script-analyze-echo-response', f'{module_name} = type=http-request,pattern='),
            (r' url script-response-body ', r',requires-body=1,script-path='),
            (r' url script-echo-response ', r',requires-body=1,script-path='),
            (r' url script-response-header ', r',requires-body=1,script-path='),
            (r' url script-request-body ', r',requires-body=1,script-path='),
            (r' url script-analyze-echo-response ', r',requires-body=1,script-path='),
            (r' url script-request-header ', r',requires-body=0,script-path='),
            (r', reject-200', r', REJECT'),
            (r', reject-img', r', REJECT'),
            (r', reject-dict', r', REJECT'),
            (r', reject-array', r', REJECT'),
            (r', reject-video', r', REJECT'),
            (r', reject-replace', r', REJECT'),
            (r'(\s,)reject\b', r'\1REJECT'),
            (r'reject-200', r'- reject'),
            (r'reject-img', r'- reject'),
            (r'reject-dict', r'- reject'),
            (r'reject-array', r'- reject'),
            (r'reject-video', r'- reject'),
            (r'reject-replace', r'- reject'),
            (r'[^,-] reject', r' - reject'),
            (r'http-response ', f'{module_name} = type=http-response,pattern='),
            (r'http-request ', f'{module_name} = type=http-request,pattern='),
            (r', tag.*', r''),
            (r' script-path = ', r',script-path='),
            (r'(\S*) 302 (\S*)', r'\1 \2 302'),
            (r'hostname =', r'Hostname = %APPEND%'),
        ],
        'loon': [
            (r'url reject-200', r'reject-200'),
            (r'url reject-img', r'reject-img'),
            (r'url reject-dict', r'reject-dict'),
            (r'url reject-array', r'reject-array'),
            (r'url reject-video', r'reject-video'),
            (r'url reject-replace', r'reject-replace'),
            (r'url reject', r'reject'),
            (r'url script-response-body', r'http-response '),
            (r'url script-echo-response', r'http-response '),
            (r'url script-response-header', r'http-response '),
            (r'url script-request-body', r'http-request '),
            (r'url script-request-header', r'http-request '),
            (r'url script-analyze-echo-response', r'http-request '),
            (r'/script-response-body/', r', requires-body = true, tag = ' + module_name),
            (r'/script-echo-response/', r', requires-body = true, tag = ' + module_name),
            (r'/script-response-header/', r', requires-body = true, tag = ' + module_name),
            (r'/script-request-body/', r', requires-body = true, tag = ' + module_name),
            (r'/script-analyze-echo-response/', r', requires-body = true, tag = ' + module_name),
            (r'/script-request-header/', r', requires-body = false, tag = ' + module_name),
            (r'url script-response-body', r'script-path='),
            (r'url script-echo-response', r'script-path='),
            (r'url script-response-header', r'script-path='),
            (r'url script-request-body', r'script-path='),
            (r'url script-request-header', r'script-path='),
            (r'url script-analyze-echo-response', r'script-path='),
            (r', tag.*', f', tag = {module_name}'),
            (r'hostname =', r'Hostname ='),
        ],
    }

    if is_surge:
        content = apply_replacements(content, replacements['surge'])
        output_file_name = f"{module_name}.sgmodule"
    else:
        content = apply_replacements(content, replacements['loon'])
        output_file_name = f"{module_name}.plugin"

    output_path = os.path.join(output_dir, output_file_name)
    with open(output_path, 'w') as output_file:
        output_file.writelines(content)

if __name__ == "__main__":
    input_file = sys.argv[1]
    module_name = sys.argv[2]
    comment = sys.argv[3]
    
    process_file(input_file, module_name, comment, 'Modules/Surge', is_surge=True)
    process_file(input_file, module_name, comment, 'Modules/Loon', is_surge=False)
