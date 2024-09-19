#!/bin/bash
input_file=$1
module_name=$2
comment=$3

# Common replacements for both Surge and Loon
sed_common="
    /raw.githubusercontent.com/ s/\/main\//\/raw\/main\//Ig
    /raw.githubusercontent.com/ s/\/master\//\/raw\/master\//Ig
    s/raw.githubusercontent.com/github.com/Ig
    s/HOST,/DOMAIN,/Ig
    s/HOST-SUFFIX,/DOMAIN-SUFFIX,/Ig
    s/HOST-KEYWORD,/DOMAIN-KEYWORD,/Ig
    s/IP-CIDR,/IP-CIDR,/Ig
    s/IP6-CIDR,/IP-CIDR6,/Ig
    /IP-CIDR/ s/\(REJECT\)\([^,]*$\)/\1, no-resolve/Ig
"

# Surge conversion
sed -e "1 i\\
$comment" \
    -e "$sed_common" \
    -e "s/url reject-200/- reject/Ig" \
    -e 's/url reject-img/- reject/Ig' \
    -e 's/url reject-dict/- reject/Ig' \
    -e 's/url reject-array/- reject/Ig' \
    -e 's/url reject-video/- reject/Ig' \
    -e 's/url reject-replace/- reject/Ig' \
    -e 's/url reject/- reject/Ig' \
    -e "/url script-response-body/ s/^/${module_name} = type=http-response,pattern=/" \
    -e "/url script-echo-response/ s/^/${module_name} = type=http-response,pattern=/" \
    -e "/url script-response-header/ s/^/${module_name} = type=http-response,pattern=/" \
    -e "/url script-request-body/ s/^/${module_name} = type=http-request,pattern=/" \
    -e "/url script-request-header/ s/^/${module_name} = type=http-request,pattern=/" \
    -e "/url script-analyze-echo-response/ s/^/${module_name} = type=http-request,pattern=/" \
    -e 's/ url script-response-body /,requires-body=1,script-path=/Ig' \
    -e 's/ url script-echo-response /,requires-body=1,script-path=/Ig' \
    -e 's/ url script-response-header /,requires-body=1,script-path=/Ig' \
    -e 's/ url script-request-body /,requires-body=1,script-path=/Ig' \
    -e 's/ url script-analyze-echo-response /,requires-body=1,script-path=/Ig' \
    -e 's/ url script-request-header /,requires-body=0,script-path=/Ig' \
    -e '/reject/ { s/\([^,]*\)reject/\1- reject/; s/, reject/ REJECT/Ig }' \
    -e "s/http-response /${module_name} = type=http-response,pattern=/" \
    -e "s/http-request /${module_name} = type=http-request,pattern=/" \
    -e '/http-response/ s/, tag.*//' \
    -e '/http-request/ s/, tag.*//' \
    -e 's/ script-path = /,script-path=/Ig' \
    -e '/302/ s/\(.*\) 302 \(.*\)/\1 \2 302/' \
    -e 's/hostname =/Hostname = %APPEND%/Ig' \
    "$input_file" > "Modules/Surge/${module_name}.sgmodule"

# Loon conversion
sed -e "1 i\\
$comment" \
    -e "$sed_common" \
    -e "s/url reject-200/reject-200/Ig" \
    -e 's/url reject-img/reject-img/Ig' \
    -e 's/url reject-dict/reject-dict/Ig' \
    -e 's/url reject-array/reject-array/Ig' \
    -e 's/url reject-video/reject-video/Ig' \
    -e 's/url reject-replace/reject-replace/Ig' \
    -e 's/url reject/reject/Ig' \
    -e "/url script-response-body/ s/^/http-response /" \
    -e "/url script-echo-response/ s/^/http-response /" \
    -e "/url script-response-header/ s/^/http-response /" \
    -e "/url script-request-body/ s/^/http-request /" \
    -e "/url script-request-header/ s/^/http-request /" \
    -e "/url script-analyze-echo-response/ s/^/http-request /" \
    -e "/script-response-body/ s/$/, requires-body = true, tag = ${module_name}/" \
    -e "/script-echo-response/ s/$/, requires-body = true, tag = ${module_name}/" \
    -e "/script-response-header/ s/$/, requires-body = true, tag = ${module_name}/" \
    -e "/script-request-body/ s/$/, requires-body = true, tag = ${module_name}/" \
    -e "/script-analyze-echo-response/ s/$/, requires-body = true, tag = ${module_name}/" \
    -e "/script-request-header/ s/$/, requires-body = false, tag = ${module_name}/" \
    -e 's/url script-response-body/script-path=/Ig' \
    -e 's/url script-echo-response/script-path=/Ig' \
    -e 's/url script-response-header/script-path=/Ig' \
    -e 's/url script-request-body/script-path=/Ig' \
    -e 's/url script-request-header/script-path=/Ig' \
    -e 's/url script-analyze-echo-response/script-path=/Ig' \
    -e 's/, tag.*/\, tag = '"${module_name}"'/' \
    -e 's/hostname =/Hostname =/Ig' \
    "$input_file" > "Modules/Loon/${module_name}.plugin"
