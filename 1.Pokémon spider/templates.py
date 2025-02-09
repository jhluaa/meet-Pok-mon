

# requests 操作加入ip池 代理 useragent cookie等手段
import io
import sys
import random
import requests
import time
import logging
from lxml import etree
from pymongo import MongoClient

# ================= 配置部分 ==================
APP_KEY = '1205511799882272768'
APP_SECRET = 'tiiUhVfw'
PROXY_API_URL = "https://api.xiaoxiangdaili.com/ip/get"
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "pokemon_database"          #数据库
MONGO_COLLECTION = "douban_collection"   # book movie music 3张表
IMAGE_SAVE_PATH = r'C:\Users\luke\Desktop\project\\'

# 豆瓣搜索的 URL（图书、电影、音乐）
SEARCH_URLS = {
    "book": "https://search.douban.com/book/subject_search?search_text=宝可梦&cat=1001",
    # "movie": "https://search.douban.com/movie/subject_search?search_text=宝可梦&cat=1002",
    # "music": "https://search.douban.com/music/subject_search?search_text=宝可梦&cat=1003",
}

# ================= 日志配置 ==================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class DoubanScraper:
    def __init__(self):
        self.search_urls = SEARCH_URLS
        self.client = MongoClient(MONGO_URI)         # 连接 MongoDB
        self.db = self.client[MONGO_DB]                # 使用/创建数据库
        self.collection = self.db[MONGO_COLLECTION]     # 使用/创建集合
        self.uapools = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.22 Safari/537.36 SE 2.X MetaSr 1.0',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)',
            'Mozilla/5.0 (compatible; ABrowse 0.4; Syllable)',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
        ]
        self.headers = {}
        self.proxies=''
        self.cookie = 'bid=c8OsiziavBU; ll="118165"; ap_v=0,6.0; loc-last-index-location-id="118165"; dbcl2="198033818:7f77Wuj7gq8"; ck=OW-m; frodotk_db="ca4a8c9a313b3ef45edfa5ce93b1bcdc"; push_noty_num=0; push_doumail_num=0'

    def get_proxy(self):
        """通过代理API获取代理IP"""
        try:
            res = requests.get(
                PROXY_API_URL,
                params={'appKey': APP_KEY, 'appSecret': APP_SECRET, 'wt': 'text', 'cnt': 1},
                timeout=30
            )
            proxy = res.text.strip()
            logging.info(f"代理 API 返回：{proxy}")
            return proxy
        except Exception as e:
            logging.error(f"获取代理失败：{e}")
            return None

    def get_ip(self):
        """构造requests请求所需的proxies参数"""
        proxy = self.get_proxy()
        if proxy:
            proxy_meta = f"http://{APP_KEY}:{APP_SECRET}@{proxy}"
            proxies = {'http': proxy_meta, 'https': proxy_meta}
            return proxies
        else:
            return None

    def get_random_headers(self):
        """获取随机的请求头，并添加 Cookie 信息"""
        random_user_agent = random.choice(self.uapools)
        headers = {"User-Agent": random_user_agent}
        if self.cookie:
            headers["Cookie"] = self.cookie
        return headers

    def get_html_content(self, url, headers, proxies):
        """请求指定URL，并返回网页HTML内容"""
        try:
            response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
            response.encoding = response.apparent_encoding
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"请求{url}失败！！！：{e}")
            return None

    def save_image(self, save_path, img_name, image_url, headers, proxies):
        """下载图片并保存到本地"""
        try:
            content = requests.get(image_url, headers=headers, proxies=proxies, timeout=10).content
            # 如果 image_url 中不包含扩展名，则默认使用 .jpg
            if not image_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                ext = '.jpg'
            else:
                ext = image_url[-4:]
            # 清理文件名中的空格或斜杠
            img_name = img_name.replace(' ', '').replace('/', '_') + ext
            with open(save_path + img_name, 'wb') as f:
                f.write(content)
            logging.info(f"图片 {img_name} 下载成功！")
        except Exception as e:
            logging.error(f"图片 {img_name} 下载失败：{e}")

    def save_to_mongo(self, data):
        """将数据保存到 MongoDB 数据库中"""
        try:
            self.collection.insert_one(data)
            logging.info(f"成功保存：{data.get('title', '无标题')} 到 MongoDB")
        except Exception as e:
            logging.error(f"保存到MongoDB失败：{e}")

    def parse_books_xp(self, html_tree):
        """
        使用 XPath 提取图书信息，返回包含字典的列表
        假设每个图书条目放在 <div class="result-item book"> 中
        """
        data_url=[]
        items = []
        book_nodes = html_tree.xpath('//*[@id="root"]/div/div[2]/div[1]/div[1]/div/div/a/@href') # 拿到url 列表
        data_url.append(book_nodes)
        for url  in data_url:
            node=self.get_html_content(url, self.headers, self.proxies)
            item = {}
            title = node.xpath('.//h3[@class="title"]/text()')
            item['title'] = title[0].strip() if title else ""
            url = node.xpath('.//a[@class="detail-link"]/@href')
            item['url'] = url[0].strip() if url else ""
            cover = node.xpath('.//img[@class="cover"]/@src')
            item['cover'] = cover[0].strip() if cover else ""
            author = node.xpath('.//span[@class="author"]/text()')
            item['author'] = author[0].strip() if author else ""
            rating = node.xpath('.//span[@class="rating"]/text()')
            item['rating'] = rating[0].strip() if rating else ""
            items.append(item)
            time.sleep(2)
        return items

    def parse_movies_xp(self, html_tree):
        """
        使用 XPath 提取电影信息，返回包含字典的列表
        假设每个电影条目放在 <div class="result-item movie"> 中
        """
        movie_nodes = html_tree.xpath('//div[contains(@class, "result-item") and contains(@class, "movie")]')
        items = []
        for node in movie_nodes:
            item = {}
            title = node.xpath('.//h3[@class="title"]/text()')
            item['title'] = title[0].strip() if title else ""
            url = node.xpath('.//a[@class="detail-link"]/@href')
            item['url'] = url[0].strip() if url else ""
            cover = node.xpath('.//img[@class="cover"]/@src')
            item['cover'] = cover[0].strip() if cover else ""
            director = node.xpath('.//span[@class="director"]/text()')
            # 对于电影，这里将导演或主演信息作为 author
            item['author'] = director[0].strip() if director else ""
            rating = node.xpath('.//span[@class="rating"]/text()')
            item['rating'] = rating[0].strip() if rating else ""
            items.append(item)
        return items

    def parse_musics_xp(self, html_tree):
        """
        使用 XPath 提取音乐信息，返回包含字典的列表
        假设每个音乐条目放在 <div class="result-item music"> 中
        """
        music_nodes = html_tree.xpath('//div[contains(@class, "result-item") and contains(@class, "music")]')
        items = []
        for node in music_nodes:
            item = {}
            title = node.xpath('.//h3[@class="title"]/text()')
            item['title'] = title[0].strip() if title else ""
            url = node.xpath('.//a[@class="detail-link"]/@href')
            item['url'] = url[0].strip() if url else ""
            cover = node.xpath('.//img[@class="cover"]/@src')
            item['cover'] = cover[0].strip() if cover else ""
            singer = node.xpath('.//span[@class="singer"]/text()')
            # 对于音乐，将歌手信息作为 author
            item['author'] = singer[0].strip() if singer else ""
            rating = node.xpath('.//span[@class="rating"]/text()')
            item['rating'] = rating[0].strip() if rating else ""
            items.append(item)
        return items

    def parse_douban_data(self, html, category):
        """
        通过 XPath 从 HTML 中提取目标数据，并根据类别调用相应的解析函数，
        返回一个包含数据字典的列表。
        """
        html_tree = etree.HTML(html)
        items = []
        if category == "book":
            items = self.parse_books_xp(html_tree)
        elif category == "movie":
            items = self.parse_movies_xp(html_tree)
        elif category == "music":
            items = self.parse_musics_xp(html_tree)
        else:
            logging.error("未知的类别")
            return []

        # 对每个提取的字典进一步处理，并记录日志
        results = []
        for item in items:
            result = {}
            result["title"] = item.get("title", "").strip()
            result["url"] = item.get("url", "")
            result["cover"] = item.get("cover", "")
            result["author"] = item.get("author", "")
            result["rating"] = item.get("rating", "")
            logging.info(f"解析到条目：{result['title']}")
            results.append(result)
        return results

    def run(self):
        """入口函数，依次爬取各类别的数据，并保存结果"""
        # 解决输出编码问题
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        for category, url in self.search_urls.items():
            logging.info(f"开始爬取豆瓣 {category} 数据，目标URL:{url}")
            self.headers = self.get_random_headers()  # 获取随机请求头
            self.proxies = self.get_ip()              # 获取代理 IP
            if category == 'book':
                root_urls = [f"{url}&start={i * 15}" for i in range(5)]  # 构造分页 URL
                for root_url in root_urls:
                    logging.info(f"爬取分页 URL: {root_url}")
                    html_content = self.get_html_content(root_url, self.headers, self.proxies)  # 获取网页内容
                    if html_content:
                        data_items = self.parse_douban_data(html_content, category)  # 解析网页数据

                        # 将解析到的数据保存到 MongoDB，并下载封面图片
                        for result in data_items:
                            self.save_to_mongo(result)  # 保存到 MongoDB
                            if result.get("cover"):
                                self.save_image(
                                    IMAGE_SAVE_PATH,
                                    result["title"],
                                    result["cover"],
                                    self.get_random_headers(),
                                    self.get_ip()
                                )
                        logging.info(f"豆瓣 {category} 数据解析完成，分页 URL: {root_url}")
                    else:
                        logging.error(f"获取豆瓣 {category} 数据失败，分页 URL: {root_url}")

                    time.sleep(10)  # 避免频繁请求被封禁

if __name__ == '__main__':
    scraper = DoubanScraper()
    scraper.run()