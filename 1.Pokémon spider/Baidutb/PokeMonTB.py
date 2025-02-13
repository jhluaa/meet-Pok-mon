import io
import sys
import random
import requests
import time
import logging
import re
from pymongo import MongoClient
from tqdm import tqdm
from lxml import  etree
APP_KEY = '1206245507182514176'
APP_SECRET = 'YJa120kF'
PROXY_API_URL = "https://api.xiaoxiangdaili.com/ip/get"

# ================= 日志配置 ==================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# tbody问题 使用正则化匹配策略
class TbScraper:
    def __init__(self):
        self.search_urls = {
            "Pokémon": "https://tieba.baidu.com/f?kw=宝可梦剑盾&ie=utf-8",
        }
        self.uapools = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.22 Safari/537.36 SE 2.X MetaSr 1.0',
        ]
        self.cookie = {
            'jsdk-uuid': '537ef82d-6630-4235-a6a4-e303c947cdb2',
            'BIDUPSID': '36342F761A1402D7F20B0E6FBD9FD152',
            'PSTM': '1734444865',
            'BAIDU_WISE_UID': 'wapp_1737937726298_602',
            'H_PS_PSSID': '60274_61027_61804_61987_62053_62064',
            'BAIDUID': '7E3381EC4665FE4D58281058E080F966:FG=1',
            'BAIDUID_BFESS': '7E3381EC4665FE4D58281058E080F966:FG=1',
            'ZFY': ':AA:BF6neSkvcoPM3RTHZVsM:AcudHG4TQ0EOSFKMF5Ftw:C',
            'wise_device': '0',
            'Hm_lvt_292b2e1608b0823c1cb6beef7243ef34': '1737937727,1739109682,1739185114',
            'HMACCOUNT': 'B06FD9D6F1D2EE5E',
            'USER_JUMP': '-1',
            'ppfuid': 'undefined',
            'video_bubble0': '1',
            'Hm_lvt_049d6c0ca81a94ed2a9b8ae61b3553a5': '1739194720',
            'Hm_lpvt_049d6c0ca81a94ed2a9b8ae61b3553a5': '1739195873',
            'arialoadData': 'false',
            'BDUSS': 'TBGWXNOOWZQbnFFWW1nTWVHaXA1TXBRaE9TWlFmVi1EUFBKNklxbGtyM3NrOUZuSVFBQUFBJCQAAAAAAAAAAAEAAAAu8MX1bHVrZWV2ZW4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOwGqmfsBqpnT',
            'BDUSS_BFESS': 'TBGWXNOOWZQbnFFWW1nTWVHaXA1TXBRaE9TWlFmVi1EUFBKNklxbGtyM3NrOUZuSVFBQUFBJCQAAAAAAAAAAAEAAAAu8MX1bHVrZWV2ZW4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOwGqmfsBqpnT',
            'STOKEN': 'cb568d25b33faff94c0a9062a9cfd297119e9aaee6650917448bc55dbe2d0de1',
            '4123389998_FRSVideoUploadTip': '1',
            'video_bubble4123389998': '1',
            'Hm_lpvt_292b2e1608b0823c1cb6beef7243ef34': '1739196191',
            'XFI': 'c3bbc930-e7b7-11ef-951c-a7a8489dbec6',
            'BA_HECTOR': '80208180800g25a4ah0h2h2gago89t1jqk1p01u',
            'XFCS': '557C1FAE7FFAB290C3FFC97EFD56E9146633706A3CB10CC7E7F01ACB2AE91B00',
            'XFT': '+7e/4kUPOSccRr5/GMJ7s4onHRdWuW0QjtAVfwy19y0=',
            'RT': '"z=1&dm=baidu.com&si=529ba208-5353-4024-9ad2-ae84f5395d99&ss=m6z2yc0v&sl=5&tt=9mw&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ld=1k1m9&ul=1k4x7"',
        }
        self.uapools = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0",
        ]
        self.all_tb_urls = []

    def get_proxy(self):
        """通过代理 API 获取代理 IP"""
        try:
            res = requests.get(PROXY_API_URL, params={'appKey': APP_KEY, 'appSecret': APP_SECRET, 'wt': 'text', 'cnt': 1}, timeout=200)
            proxy = res.text.strip()
            logging.info(f"获取代理：{proxy}")
            return proxy
        except requests.RequestException as e:
            logging.error(f"获取代理失败：{e}")
            return None

    def get_ip(self):
        """构造 requests 代理参数"""
        proxy = self.get_proxy()
        if proxy:
            proxy_meta = f"http://{APP_KEY}:{APP_SECRET}@{proxy}"
            return {'http': proxy_meta, 'https': proxy_meta}
        return None

    def get_random_headers(self):
        """获取随机请求头"""
        # headers = {"User-Agent": random.choice(self.uapools)}
        headers = {
        "User-Agent": random.choice(self.uapools)
        }
        if self.cookie:
            headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookie.items())
        return headers
    def fetch_page_content(self, url, headers=None, retries=3):
        """获取网页内容并重用代理"""
        headers = headers or self.get_random_headers()
        proxies = self.current_proxies
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
                response.encoding = response.apparent_encoding
                return response.text
            except requests.RequestException as e:
                time.sleep(5)
                logging.warning(f"请求 {url} 失败 ({attempt + 1}/{retries})，更换代理：{e}")
                proxies = self.get_ip()
                self.current_proxies = proxies



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
        url_counter = 0  # 计数器，统计已爬取URL数量
        for category, url in self.search_urls.items():
            logging.info(f"开始爬取贴吧 {category} ，目标URL: {url}")
            # 每爬取 10 个 URL 更换一次代理
            if url_counter % 20 == 0:
                self.current_proxies = self.get_ip()
                logging.info(f"切换代理，新代理: {self.current_proxies}")
            url_counter += 1
            for i in range(0, 67801, 50):
                root_url = f"{url}&pn={i}"
                logging.info(f"爬取分页 URL: {root_url}")
                html_content = self.fetch_page_content(root_url)
                if html_content:
                    self.parse_tburl_re(html_content)
                time.sleep(random.uniform(1, 4))  # 随机延时 1-4 秒，避免被反爬机制封禁
        self.save_url()  # 保存所有抓取到的 URL




class TbdataScraper:
    def __init__(self, input_file="urls.txt"):
        """
        初始化爬虫类
        :param input_file: 存储图书链接的文件名
        """
        self.input_file = input_file
        self.TB_urls = self.load_urls_from_file()  #贴吧URL列表
        self.TB_details = []  # 存储贴吧评论详细信息
        self.cookie = {
            'jsdk-uuid': '537ef82d-6630-4235-a6a4-e303c947cdb2',
            'BIDUPSID': '36342F761A1402D7F20B0E6FBD9FD152',
            'PSTM': '1734444865',
            'BAIDU_WISE_UID': 'wapp_1737937726298_602',
            'H_PS_PSSID': '60274_61027_61804_61987_62053_62064',
            'BAIDUID': '7E3381EC4665FE4D58281058E080F966:FG=1',
            'BAIDUID_BFESS': '7E3381EC4665FE4D58281058E080F966:FG=1',
            'ZFY': ':AA:BF6neSkvcoPM3RTHZVsM:AcudHG4TQ0EOSFKMF5Ftw:C',
            'wise_device': '0',
            'Hm_lvt_292b2e1608b0823c1cb6beef7243ef34': '1737937727,1739109682,1739185114',
            'HMACCOUNT': 'B06FD9D6F1D2EE5E',
            'USER_JUMP': '-1',
            'ppfuid': 'undefined',
            'video_bubble0': '1',
            'Hm_lvt_049d6c0ca81a94ed2a9b8ae61b3553a5': '1739194720',
            'Hm_lpvt_049d6c0ca81a94ed2a9b8ae61b3553a5': '1739195873',
            'arialoadData': 'false',
            'BDUSS': 'TBGWXNOOWZQbnFFWW1nTWVHaXA1TXBRaE9TWlFmVi1EUFBKNklxbGtyM3NrOUZuSVFBQUFBJCQAAAAAAAAAAAEAAAAu8MX1bHVrZWV2ZW4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOwGqmfsBqpnT',
            'BDUSS_BFESS': 'TBGWXNOOWZQbnFFWW1nTWVHaXA1TXBRaE9TWlFmVi1EUFBKNklxbGtyM3NrOUZuSVFBQUFBJCQAAAAAAAAAAAEAAAAu8MX1bHVrZWV2ZW4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOwGqmfsBqpnT',
            'STOKEN': 'cb568d25b33faff94c0a9062a9cfd297119e9aaee6650917448bc55dbe2d0de1',
            '4123389998_FRSVideoUploadTip': '1',
            'video_bubble4123389998': '1',
            'Hm_lpvt_292b2e1608b0823c1cb6beef7243ef34': '1739196191',
            'XFI': 'c3bbc930-e7b7-11ef-951c-a7a8489dbec6',
            'BA_HECTOR': '80208180800g25a4ah0h2h2gago89t1jqk1p01u',
            'XFCS': '557C1FAE7FFAB290C3FFC97EFD56E9146633706A3CB10CC7E7F01ACB2AE91B00',
            'XFT': '+7e/4kUPOSccRr5/GMJ7s4onHRdWuW0QjtAVfwy19y0=',
            'RT': '"z=1&dm=baidu.com&si=529ba208-5353-4024-9ad2-ae84f5395d99&ss=m6z2yc0v&sl=5&tt=9mw&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ld=1k1m9&ul=1k4x7"',
        }
        self.uapools = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0",
        ]
        # 初始时获取一次代理
        self.current_proxies = self.get_ip()

    def get_proxy(self):
        """通过代理 API 获取代理 IP"""
        try:
            res = requests.get(PROXY_API_URL, params={'appKey': APP_KEY, 'appSecret': APP_SECRET, 'wt': 'text', 'cnt': 1}, timeout=200)
            proxy = res.text.strip()
            logging.info(f"获取代理：{proxy}")
            return proxy
        except requests.RequestException as e:
            logging.error(f"获取代理失败：{e}")
            return None

    def get_ip(self):
        """构造 requests 代理参数"""
        proxy = self.get_proxy()
        if proxy:
            proxy_meta = f"http://{APP_KEY}:{APP_SECRET}@{proxy}"
            return {'http': proxy_meta, 'https': proxy_meta}
        return None

    def get_random_headers(self):
        """获取随机请求头"""
        # headers = {"User-Agent": random.choice(self.uapools)}
        headers = {
        "User-Agent": random.choice(self.uapools)
        }
        if self.cookie:
            headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookie.items())
        return headers


    def fetch_page_content(self, url, headers=None, retries=3):
        """获取网页内容并重用代理"""
        headers = headers or self.get_random_headers()
        proxies = self.current_proxies
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
                response.encoding = response.apparent_encoding
                return response.text
            except requests.RequestException as e:
                time.sleep(3)
                logging.warning(f"请求 {url} 失败 ({attempt + 1}/{retries})，更换代理：{e}")
                proxies = self.get_ip()
                self.current_proxies = proxies

        return None

    def load_urls_from_file(self):
        """从文件读取书籍 URL"""
        try:
            with open(self.input_file, "r", encoding="utf-8") as file:
                urls = [line.strip() for line in file if line.strip()]
            logging.info(f"加载 {len(urls)} 个贴吧URL")
            return urls
        except Exception as e:
            logging.error(f"读取 {self.input_file} 失败：{e}")
            return []

    def parse_tieba_xp(self, html, url):
        """解析贴吧信息"""
        html_tree = etree.HTML(html)
        # 获取所有匹配的 <div> 节点
        comment_nodes = html_tree.xpath(
            '//div[contains(concat(" ", normalize-space(@class), " "), " d_post_content ") and ' +
            'contains(concat(" ", normalize-space(@class), " "), " j_d_post_content ")]'
        )

        # 对每个节点提取所有文本，并去除多余空白
        comment_texts = [node.xpath('string(.)').strip() for node in comment_nodes]

        # 将所有评论文本合并为一个字符串（可以用换行分隔，也可以用其它分隔符）
        all_comments = "\n".join(comment_texts)

        item = {
            'title': html_tree.xpath('//h3/text()')[0].strip() if html_tree.xpath('//h3/text()') else "",
            'url': url.strip(),
            'comment':all_comments
        }
        time.sleep(random.uniform(1, 3))
        return item

    def save_to_mongo(self, data, collection):
        """保存到 MongoDB"""
        try:
            collection.update_one({'url': data['url']}, {'$set': data}, upsert=True)
            logging.info(f"保存到 MongoDB：{data.get('title', '未知标题')}")
        except Exception as e:
            logging.error(f"MongoDB 存储失败：{e}")

    def run(self):
        """爬虫主逻辑"""
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]

        url_counter = 0  # 计数器，统计已爬取 URL 数量

        for url in tqdm(self.TB_urls, desc="爬取进度"):
            # 如果数据已存在，则跳过
            if collection.find_one({"url": url}):
                logging.info(f"已存在：{url}，跳过")
                continue

            # 每爬取 10 个 URL 更换一次代理
            if url_counter % 20 == 0:
                self.current_proxies = self.get_ip()
                logging.info(f"切换代理，新代理: {self.current_proxies}")
            url_counter += 1

            html = self.fetch_page_content(url)
            if not html:
                logging.warning(f"无法获取 {url} 的内容")
                continue

            detail = self.parse_tieba_xp(html, url)
            if not detail:
                logging.warning(f"未能提取 {url} 的详细信息")
                continue

            self.TB_details.append(detail)
            self.save_to_mongo(detail, collection)

            time.sleep(random.uniform(1, 3))

        logging.info(f"爬取完成，共提取 {len(self.TB_details)} 条贴吧评论")


if __name__ == '__main__':
    # scraper = TbScraper() # urls链接
    # scraper.run()
    MONGO_URI = "mongodb://localhost:27017/"
    MONGO_DB = "pokemon_database"  # 数据库
    MONGO_COLLECTION = "Tieba_pokemon_jiandun"
    scraper = TbdataScraper(input_file="urls.txt")
    scraper.run()
