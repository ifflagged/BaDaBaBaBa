# 来源：https://github.com/QingRex/LoonKissSurge/blob/main/script.py

import requests
import re

# 下载并保存README.md文件
def download_md_file(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'w', encoding='utf-8') as file:
            file.write(response.text)
        print("Markdown 文件下载成功")
    else:
        print(f"下载失败，状态码: {response.status_code}")

# 提取链接和标题
def extract_links_and_titles(md_file_path):
    with open(md_file_path, 'r', encoding='utf-8') as file:
        content = file.readlines()

    # 正则表达式匹配<td><a href="URL">标题</a></td>
    pattern = re.compile(r'<td><a href="https://www.nsloon.com/openloon/import\?plugin=([^"]+)">([^<]+)</a></td>')

    results = []

    for line in content:
        match = pattern.search(line)
        if match:
            plugin_link = match.group(1)
            title = match.group(2)
            results.append((title, plugin_link))

    return results

# 请求插件并保存结果
def request_and_save_plugins(links_and_titles):
    for title, plugin_link in links_and_titles:
        # 构造请求URL
        url = f"http://localhost:9101/file/_start_/{plugin_link}/_end_/Weibo_remove_ads.sgmodule.txt?type=loon-plugin&target=loon-plugin&sni=%20%2C%20&del=true&pm=REJECT&category=iKeLee"

        response = requests.get(url)
        if response.status_code == 200:
            # 保存返回的结果为 title.plugin
            file_name = f"{title}.plugin"
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(response.text)
            print(f"插件 {title} 已保存为 {file_name}")
        else:
            print(f"请求失败，插件 {title} 状态码: {response.status_code}")

# 主函数
def main():
    md_url = "https://raw.githubusercontent.com/luestr/ProxyResource/refs/heads/main/README.md"
    md_file_path = "README.md"

    download_md_file(md_url, md_file_path)

    links_and_titles = extract_links_and_titles(md_file_path)

    request_and_save_plugins(links_and_titles)

if __name__ == "__main__":
    main()
