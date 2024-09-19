#!/bin/bash

input_file=$1
module_name=$2
comment=$3

# 输出目录
surge_output_dir="Modules/Surge"
loon_output_dir="Modules/Loon"

# 创建输出目录
mkdir -p "$surge_output_dir"
mkdir -p "$loon_output_dir"

# Surge 和 Loon 文件初始化
surge_output_file="$surge_output_dir/${module_name}.sgmodule"
loon_output_file="$loon_output_dir/${module_name}.plugin"

# 清空或创建输出文件
> "$surge_output_file"
> "$loon_output_file"

# 处理 Header Rewrite 的转换逻辑
process_header_rewrite() {
  local line=$1
  local url_regex
  local script_url
  local script_type
  local requires_body

  if [[ $line =~ (http-response|http-request) ]]; then
    script_type=${BASH_REMATCH[1]}
  elif [[ $line =~ script-response-body|script-echo-response|script-response-header ]]; then
    script_type="http-response"
  else
    script_type="http-request"
  fi

  url_regex=$(echo "$line" | grep -oP '^https?:\/\/[^\s]+')
  script_url=$(echo "$line" | grep -oP 'https:\/\/[^\s]+')
  requires_body="false"

  if [[ $line =~ script-response-body|script-echo-response|script-response-header|script-request-body|script-analyze-echo-response ]]; then
    requires_body="true"
  fi

  # Surge 格式输出
  echo "type=$script_type,pattern=$url_regex,requires-body=$requires_body,script-path=$script_url" >> "$surge_output_file"
  
  # Loon 格式输出
  echo "$script_type $url_regex script-path=$script_url, requires-body=$requires_body, tag=$module_name" >> "$loon_output_file"
}

# 处理 URL Rewrite 的转换逻辑
process_url_rewrite() {
  local line=$1
  local surge_rewrite
  local loon_rewrite

  surge_rewrite=$(echo "$line" | sed 's/ url reject/- reject/')
  loon_rewrite=$(echo "$line" | sed 's/ url reject-/- reject-/')

  echo "$surge_rewrite" >> "$surge_output_file"
  echo "$loon_rewrite" >> "$loon_output_file"
}

# 处理 Rule 的转换逻辑
process_rule() {
  local line=$1
  local surge_rule
  local loon_rule

  surge_rule=$(echo "$line" | sed -e 's/HOST/DOMAIN/g' -e 's/HOST-SUFFIX/DOMAIN-SUFFIX/g' -e 's/HOST-KEYWORD/DOMAIN-KEYWORD/g' -e 's/IP6/IP-CIDR6/g' -e 's/^;/#/')
  loon_rule=$(echo "$line" | sed -e 's/HOST/DOMAIN/g' -e 's/HOST-SUFFIX/DOMAIN-SUFFIX/g' -e 's/HOST-KEYWORD/DOMAIN-KEYWORD/g' -e 's/IP6/IP-CIDR6/g')

  echo "$surge_rule" >> "$surge_output_file"
  echo "$loon_rule" >> "$loon_output_file"
}

# 处理 URL 的转换逻辑
process_url() {
  local line=$1
  local surge_url
  local loon_url

  surge_url=$(echo "$line" | sed 's/raw.githubusercontent.com/github.com\/RuCu6\/QuanX\/raw/g')
  loon_url=$surge_url  # Loon 和 Surge 对 URL 的处理相同

  echo "$surge_url" >> "$surge_output_file"
  echo "$loon_url" >> "$loon_output_file"
}

# 处理 MITM 的转换逻辑
process_mitm() {
  local line=$1

  # Surge 输出
  echo "Hostname = %APPEND% $line" >> "$surge_output_file"

  # Loon 输出
  echo "Hostname = $line" >> "$loon_output_file"
}

# 逐行读取文件并处理
while IFS= read -r line; do
  # 跳过空行
  [[ -z "$line" ]] && continue

  if [[ $line =~ ^http ]]; then
    process_header_rewrite "$line"
  elif [[ $line =~ url ]]; then
    process_url_rewrite "$line"
  elif [[ $line =~ ^HOST || $line =~ ^IP || $line =~ ^";HOST" ]]; then
    process_rule "$line"
  elif [[ $line =~ ^https ]]; then
    process_url "$line"
  elif [[ $line =~ ^hostname ]]; then
    process_mitm "$line"
  fi
done < "$input_file"
