#!/bin/bash
input_file=$1
module_name=$2
comment=$3

# Common replacements for both Surge and Loon
sed_common="
    s/raw.githubusercontent.com/github.com/Ig
    s/\/main\//\/raw\/main\//Ig
    s/\/master\//\/raw\/master\//Ig
    s/HOST,/DOMAIN,/Ig
    s/HOST-SUFFIX,/DOMAIN-SUFFIX,/Ig
    s/HOST-KEYWORD,/DOMAIN-KEYWORD,/Ig
    s/IP-CIDR,/IP-CIDR,/Ig
    s/IP6-CIDR,/IP-CIDR6,/Ig
    s/, REJECT/, REJECT, no-resolve/Ig
"

# Surge conversion
sed -e "1 i $comment" \
    -e "$sed_common" \
    -e 's/url reject-dict/- reject/Ig' \
    -e "s/url reject-200/- reject/Ig" \
    -e 's/url reject/- reject/Ig' \
    -e "/url script-response-body/ s/^/${module_name} = type=http-response,pattern=/" \
    -e "/url script-response-header/ s/^/${module_name} = type=http-response,pattern=/" \
    -e "/url script-request-body/ s/^/${module_name} = type=http-request,pattern=/" \
    -e 's/ url script-response-body /,requires-body=1,script-path=/Ig' \
    -e 's/ url script-response-header /,requires-body=0,script-path=/Ig' \
    -e 's/ url script-request-body /,requires-body=1,script-path=/Ig' \
    -e 's/hostname =/Hostname = %APPEND%/Ig' \
    $input_file > Modules/Surge/${module_name}.sgmodule

# Loon conversion
sed -e "1 i $comment" \
    -e "$sed_common" \
    -e 's/url reject-dict/reject-dict/Ig' \
    -e "s/url reject-200/reject-200/Ig" \
    -e 's/url reject/reject/Ig' \
    -e "/url script-response-body/ s/^/http-response /" \
    -e "/url script-response-header/ s/^/http-response /" \
    -e "/url script-request-body/ s/^/http-request /" \
    -e "/-body/ s/$/, requires-body = true, tag = ${module_name}/" \
    -e "/-header/ s/$/, requires-body = false, tag = ${module_name}/" \
    -e 's/url script-response-body/script-path=/Ig' \
    -e 's/url script-response-header/script-path=/Ig' \
    -e 's/url script-request-body/script-path=/Ig' \
    -e 's/hostname =/Hostname = /Ig' \
    $input_file > Modules/Loon/${module_name}.plugin
