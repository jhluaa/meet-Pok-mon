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
############################1.修改api_key#########################
APP_KEY = '1207892429215518720'   
APP_SECRET = '8NpvPHne'
PROXY_API_URL = "https://api.xiaoxiangdaili.com/ip/get"

# ================= 日志配置 ==================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# tbody问题 使用正则化匹配策略
class TbScraper:
    def __init__(self):
         ############################修改url 朱紫 ， 口袋妖怪 . ########################
        self.search_urls = {
            "Pokémon": "https://tieba.baidu.com/f?kw=口袋妖怪&ie=utf-8",
        }
        
        ############################修改cookie#########################
        self.cookie = {
            'BIDUPSID': '3BFB34CC9BCB40788BBDFB710531D313',
            'PSTM': '1732682521',
            'BAIDUID': '3BFB34CC9BCB40788BBDFB710531D313:SL=0:NR=10:FG=1',
            'newlogin': '1',
            'BDUSS': 'zdqd002a1NGN1JuSXY1SFJmSERaVi1BcHY5THIxUGoydngyblJSdXhTOXctcnRuSVFBQUFBJCQAAAAAAAAAAAEAAABi9Id8c2hhbW9hYWE2MzAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHBtlGdwbZRnR',
            'BDUSS_BFESS': 'zdqd002a1NGN1JuSXY1SFJmSERaVi1BcHY5THIxUGoydngyblJSdXhTOXctcnRuSVFBQUFBJCQAAAAAAAAAAAEAAABi9Id8c2hhbW9hYWE2MzAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHBtlGdwbZRnR',
            'MAWEBCUID': 'web_eqgOMiGboLHthVfzwuZrFMyGQVsxTdRbnZtTxjHIutJkHneNpM',
            'H_WISE_SIDS_BFESS': '61027_61675_61863_61985',
            'BAIDUID_BFESS': '3BFB34CC9BCB40788BBDFB710531D313:SL=0:NR=10:FG=1',
            'H_WISE_SIDS': '61027_61675_61863_61985_62064_62060_62090_62111_62126',
            'BDORZ': 'B490B5EBF6F3CD402E515D22BCDA1598',
            'BDRCVFR[feWj1Vr5u3D]': 'I67x6TjHwwYf0',
            'delPer': '0',
            'STOKEN': '47a088cbbc3ea2dec1f8ccaae63a6cfa32f797971498bf80cdcb049ff1dc0c21',
            'BAIDU_WISE_UID': 'wapp_1739520022096_294',
            'USER_JUMP': '-1',
            'Hm_lvt_292b2e1608b0823c1cb6beef7243ef34': '1739520023',
            'HMACCOUNT': '4DD7545B5D4A2D49',
            'st_key_id': '17',
            'arialoadData': 'false',
            '2089284706_FRSVideoUploadTip': '1',
            'video_bubble2089284706': '1',
            'ZFY': 'xydME51mcTDOnkBRf5Fagq7r:AahvsRKai:BzqwYgGvJM:C',
            'PSINO': '5',
            'wise_device': '0',
            'H_PS_PSSID': '61027_61675_61985_62064_62060_62090_62111_62126_62162_62167_62177_62185_62186_62195',
            'Hm_lpvt_292b2e1608b0823c1cb6beef7243ef34': '1739545406',
            'XFI': 'd82b63a0-eae4-11ef-adcd-7d9297b0a58a',
            'BA_HECTOR': '2h8l058k000gal8l00ak002lb9al221jqumpv1v',
            'ab_sr': '1.0.1_NGUxNjJhODI3YWViM2MwZDNkY2NjNjNjOWY0ZTdjZWE5Y2MyY2Y3ZGE0Mjg4OWIzNTQ0NWVkZThkM2U0ZDgzZGI3ODg4MzQ5MWI5YzNiY2ZhZTQxMDYxMDNjNDgxYjJmOGYzZDhlY2ZhYjcyY2YyNDgzZGFiMTBiYTIzNjkzZTUzNjg2MmZmMjUxMzZkNzIwMzM4MGQ4MDBmNGNjMjA4NzlmODEwM2RlZWIxNGMzZTk1Y2Y3NDNhMGI3YzkyZDgw',
            'st_data': 'a9c7c7e2571bb28ca7057d413f11898ea349172fcff654a77c96c104fce459a2b94d12b5095d69b04d2a09d48a06267bf9e39bb122c91ae5aa14754c5c3e107e400ed3b0f7f8e6072db8f36b3a6c2e31321c690b7a9c1a7496e8ed19a834615aeef69de487f767e1cdf0355229b7986c07f32d101bc4f02e78f68aaa06c68550d636c86f62fd37d06e8ae082c46ea8b6',
            'st_sign': '1c4c80b2',
            'XFCS': 'F00000A85C4A7926F071EF0070A9B5D9F06A871105FECCEC42115413E7A73D90',
            'XFT': 'bd/5a0qzc9JIQxZIHFXhj6v347ks927WNb6/Kt0hjZA=',
            'RT': '"z=1&dm=baidu.com&si=7e99bd80-203c-4a97-8b0a-aa440027adbf&ss=m74hb1a1&sl=1c&tt=vzp&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ld=f8vx4&ul=fbnhk"'
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
                time.sleep(2)
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

            # 实时写入到txt文件中
            with open("urls.txt", "a", encoding="utf-8") as f:
                for url in full_urls:
                    f.write(url + "\n")

            logging.info(f"提取到 {len(full_urls)} 个帖子 URL，并已写入文件")
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
               ############################尾页+1  905600+1########################
            for i in range(0, 905601, 50):
                root_url = f"{url}&pn={i}"
                logging.info(f"爬取分页 URL: {root_url}")
                html_content = self.fetch_page_content(root_url)
                if html_content:
                    self.parse_tburl_re(html_content)
                time.sleep(random.uniform(1, 4))  # 随机延时 1-4 秒，避免被反爬机制封禁
        # self.save_url()  # 保存所有抓取到的 URL




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
            'BIDUPSID': '3BFB34CC9BCB40788BBDFB710531D313',
            'PSTM': '1732682521',
            'BAIDUID': '3BFB34CC9BCB40788BBDFB710531D313:SL=0:NR=10:FG=1',
            'newlogin': '1',
            'BDUSS': 'zdqd002a1NGN1JuSXY1SFJmSERaVi1BcHY5THIxUGoydngyblJSdXhTOXctcnRuSVFBQUFBJCQAAAAAAAAAAAEAAABi9Id8c2hhbW9hYWE2MzAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHBtlGdwbZRnR',
            'BDUSS_BFESS': 'zdqd002a1NGN1JuSXY1SFJmSERaVi1BcHY5THIxUGoydngyblJSdXhTOXctcnRuSVFBQUFBJCQAAAAAAAAAAAEAAABi9Id8c2hhbW9hYWE2MzAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHBtlGdwbZRnR',
            'MAWEBCUID': 'web_eqgOMiGboLHthVfzwuZrFMyGQVsxTdRbnZtTxjHIutJkHneNpM',
            'H_WISE_SIDS_BFESS': '61027_61675_61863_61985',
            'BAIDUID_BFESS': '3BFB34CC9BCB40788BBDFB710531D313:SL=0:NR=10:FG=1',
            'H_WISE_SIDS': '61027_61675_61863_61985_62064_62060_62090_62111_62126',
            'BDORZ': 'B490B5EBF6F3CD402E515D22BCDA1598',
            'BDRCVFR[feWj1Vr5u3D]': 'I67x6TjHwwYf0',
            'delPer': '0',
            'STOKEN': '47a088cbbc3ea2dec1f8ccaae63a6cfa32f797971498bf80cdcb049ff1dc0c21',
            'BAIDU_WISE_UID': 'wapp_1739520022096_294',
            'USER_JUMP': '-1',
            'Hm_lvt_292b2e1608b0823c1cb6beef7243ef34': '1739520023',
            'HMACCOUNT': '4DD7545B5D4A2D49',
            'st_key_id': '17',
            'arialoadData': 'false',
            '2089284706_FRSVideoUploadTip': '1',
            'video_bubble2089284706': '1',
            'ZFY': 'xydME51mcTDOnkBRf5Fagq7r:AahvsRKai:BzqwYgGvJM:C',
            'PSINO': '5',
            'wise_device': '0',
            'H_PS_PSSID': '61027_61675_61985_62064_62060_62090_62111_62126_62162_62167_62177_62185_62186_62195',
            'Hm_lpvt_292b2e1608b0823c1cb6beef7243ef34': '1739545406',
            'XFI': 'd82b63a0-eae4-11ef-adcd-7d9297b0a58a',
            'BA_HECTOR': '2h8l058k000gal8l00ak002lb9al221jqumpv1v',
            'ab_sr': '1.0.1_NGUxNjJhODI3YWViM2MwZDNkY2NjNjNjOWY0ZTdjZWE5Y2MyY2Y3ZGE0Mjg4OWIzNTQ0NWVkZThkM2U0ZDgzZGI3ODg4MzQ5MWI5YzNiY2ZhZTQxMDYxMDNjNDgxYjJmOGYzZDhlY2ZhYjcyY2YyNDgzZGFiMTBiYTIzNjkzZTUzNjg2MmZmMjUxMzZkNzIwMzM4MGQ4MDBmNGNjMjA4NzlmODEwM2RlZWIxNGMzZTk1Y2Y3NDNhMGI3YzkyZDgw',
            'st_data': 'a9c7c7e2571bb28ca7057d413f11898ea349172fcff654a77c96c104fce459a2b94d12b5095d69b04d2a09d48a06267bf9e39bb122c91ae5aa14754c5c3e107e400ed3b0f7f8e6072db8f36b3a6c2e31321c690b7a9c1a7496e8ed19a834615aeef69de487f767e1cdf0355229b7986c07f32d101bc4f02e78f68aaa06c68550d636c86f62fd37d06e8ae082c46ea8b6',
            'st_sign': '1c4c80b2',
            'XFCS': 'F00000A85C4A7926F071EF0070A9B5D9F06A871105FECCEC42115413E7A73D90',
            'XFT': 'bd/5a0qzc9JIQxZIHFXhj6v347ks927WNb6/Kt0hjZA=',
            'RT': '"z=1&dm=baidu.com&si=7e99bd80-203c-4a97-8b0a-aa440027adbf&ss=m74hb1a1&sl=1c&tt=vzp&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ld=f8vx4&ul=fbnhk"'
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
        # time.sleep(random.uniform(1, 3))
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

            time.sleep(random.uniform(0.5, 1))

        logging.info(f"爬取完成，共提取 {len(self.TB_details)} 条贴吧评论")


if __name__ == '__main__':
    # scraper = TbScraper() # urls链接
    # scraper.run()
    MONGO_URI = "mongodb://localhost:27017/"
    MONGO_DB = "pokemon_database"  # 数据库
    MONGO_COLLECTION = "Tieba_pokemon_KDYG"
    scraper = TbdataScraper(input_file="urls.txt")
    scraper.run()
