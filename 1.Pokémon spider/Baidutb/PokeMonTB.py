import io
import sys
import random
import requests
import time
import logging
from bs4 import BeautifulSoup
import re
# ================= 日志配置 ==================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class TbScraper:
    def __init__(self):
        self.search_urls = {
            "Pokémon": "https://tieba.baidu.com/f?kw=宝可梦&ie=utf-8",
        }
        self.uapools = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.22 Safari/537.36 SE 2.X MetaSr 1.0',
        ]
        self.all_tb_urls = []

    def get_random_headers(self):
        """获取随机的请求头"""
        random_user_agent = random.choice(self.uapools)
        return {"User-Agent": random_user_agent}

    def get_html_content(self, url, headers):
        """请求指定URL，并返回网页HTML内容"""
        try:
            response = requests.get(url, headers=headers, timeout=20)
            response.encoding = 'utf-8'
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"请求 {url} 失败：{e}")
            return None



    def parse_tburl_re(self, html_content):
        """使用正则表达式提取帖子 URL，并保存到 all_tb_urls 列表中"""
        try:
            # 正则模式，匹配 /p/ 后面跟随数字的部分
            pattern = r'/p/\d+'
            urls = re.findall(pattern, html_content)

            # 去重并拼接成完整的 URL
            full_urls = [f"https://tieba.baidu.com{url}" for url in set(urls)]
            self.all_tb_urls.extend(full_urls)

            logging.info(f"提取到 {len(full_urls)} 个帖子 URL")
        except Exception as e:
            logging.error(f"正则解析失败: {e}")

    def save_url(self, file_path="urls.txt"):
        """将 all_tb_urls 列表中的所有 URL 保存到本地文本文件"""
        with open(file_path, "w", encoding="utf-8") as f:
            for url in self.all_tb_urls:
                f.write(url + "\n")
        logging.info(f"所有帖子 URL 已保存到 {file_path}")

    def run(self):
        """入口函数，爬取所有分页的 URL，并保存结果"""
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        for category, url in self.search_urls.items():
            logging.info(f"开始爬取贴吧 {category} ，目标URL: {url}")
            self.headers = self.get_random_headers()
            for i in range(0, 9201, 50):
                root_url = f"{url}&pn={i}"
                logging.info(f"爬取分页 URL: {root_url}")
                html_content = self.get_html_content(root_url, self.headers)
                if html_content:
                    self.parse_tburl_re(html_content)
                time.sleep(random.uniform(3, 7))  # 随机延时 3-7 秒，避免被反爬机制封禁
        self.save_url()  # 保存所有抓取到的 URL


if __name__ == '__main__':
    scraper = TbScraper()
    scraper.run()
