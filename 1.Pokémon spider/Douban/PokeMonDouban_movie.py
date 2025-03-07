from playwright.sync_api import sync_playwright
from lxml import etree
import time
import requests
from pymongo import MongoClient
import logging
import  random
import os
IMAGE_SAVE_PATH= '../'

APP_KEY = '1205511799882272768'
APP_SECRET = 'tiiUhVfw'
PROXY_API_URL = "https://api.xiaoxiangdaili.com/ip/get"
import pandas as pd
class DoubanScraper:
    def __init__(self, base_url,max_pages=5,output_file="urls.txt"):
        """
        初始化 DoubanScraper 类
        :param base_url: 豆瓣基础搜索 URL
        :param max_pages: 爬取的最大分页数
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.all_urls = []  # 用于存储所有爬取到的电影链接
        self.output_file = output_file


    def get_root_urls(self):
        """
        构造分页 URL 列表
        :return: 分页 URL 列表
        """
        root_urls = [f"{self.base_url}&start={i * 15}" for i in range(self.max_pages)]
        return root_urls

    def fetch_page_content(self, url):
        """
        使用 Playwright 爬取网页内容
        :param url: 需要爬取的 URL
        :return: 网页 HTML 内容
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            try:
                print(f"正在爬取页面：{url}")
                page.goto(url, timeout=60000)
                page.wait_for_selector('#root div div div div a', timeout=15000)

                # 模拟下拉操作，确保加载更多数据
                for _ in range(3):
                    page.mouse.wheel(0, 2000)
                    page.wait_for_timeout(1000)

                content = page.content()
                browser.close()
                return content

            except Exception as e:
                print(f"获取页面失败：{e}")
                browser.close()
                return None

    def parse_urls(self, html_content):
        """
        解析网页内容，提取电影链接
        :param html_content: 网页 HTML 内容
        :return: 提取到的电影链接列表
        """
        html_tree = etree.HTML(html_content)
        book_urls = html_tree.xpath('//*[@id="root"]//div/div/div/div[1]/a/@href')
        unique_urls = list(set(book_urls))  # 去重
        return unique_urls

    def save_urls_to_file(self):
        """ 将所有电影链接保存到本地 txt 文件 """
        with open(self.output_file, "w", encoding="utf-8") as file:
            for url in self.all_urls:
                file.write(url + "\n")
        print(f"所有电影链接已保存到 {self.output_file}")
    def run(self):
        """
        主流程，依次爬取分页 URL，提取并存储电影链接
        """
        root_urls = self.get_root_urls()
        for url in root_urls:
            html_content = self.fetch_page_content(url)
            if html_content:
                page_urls = self.parse_urls(html_content)
                self.all_urls.extend(page_urls)
                print(f"解析到 {len(page_urls)} 个电影链接。")
            time.sleep(5)  # 避免频繁请求被封禁

        # 去重并输出所有链接
        self.all_urls = list(set(self.all_urls))
        print(f"共解析到 {len(self.all_urls)} 个唯一电影链接。")
        self.save_urls_to_file()


class MovieDetailsScraper:
    def __init__(self, input_file="urls.txt", output_csv="movie_details.csv"):
        """
        初始化 BookDetailsScraper 类
        :param input_file: 存储电影链接的文件名
        """
        self.input_file = input_file
        self.book_urls = self.load_urls_from_file()
        self.book_details = []  # 存储电影详细信息
        self.output_csv = output_csv  # 保存到 CSV 的文件路径
        # 初始化 MongoDB 连接
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB]
        self.collection = self.db[MONGO_COLLECTION]

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

    def load_urls_from_file(self):
        """从本地 txt 文件中读取电影链接"""
        try:
            with open(self.input_file, "r", encoding="utf-8") as file:
                urls = [line.strip() for line in file if line.strip()]
            logging.info(f"从 {self.input_file} 读取到 {len(urls)} 个电影链接。")
            return urls
        except Exception as e:
            logging.error(f"读取 {self.input_file} 文件失败：{e}")
            return []

    def fetch_page_content(self, url):
        """使用 Playwright 爬取单个电影详情页面的内容"""
        proxy = self.get_proxy()
        proxy_config={}
        if proxy:
            proxy_config = {
                "server": f"http://{proxy}",
                "username": APP_KEY,
                "password": APP_SECRET
            }
        with sync_playwright() as p:
            # browser = p.chromium.launch(headless=False, proxy=proxy_config)
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            try:
                logging.info(f"正在爬取电影详情：{url}")
                page.goto(url, timeout=60000)
                page.wait_for_selector("body", state="attached", timeout=15000)  # 等待页面的 <body> 加载完成
                content = page.content()
                browser.close()
                return content
            except Exception as e:
                logging.error(f"获取电影详情页面失败：{e}")
                browser.close()
                return None

    def fetch_reviews(self, reviews_url):
        """
        使用 Playwright 爬取评论页面，点击 “展开” 按钮，提取所有评论内容
        """
        proxy = self.get_proxy()
        proxy_config={}
        if proxy:
            proxy_config = {
                "server": f"http://{proxy}",
                "username": APP_KEY,
                "password": APP_SECRET
            }
        with sync_playwright() as p:
            # browser = p.chromium.launch(headless=False, proxy=proxy_config)  # 调试时可以设为 False
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            try:
                logging.info(f"正在爬取评论页面：{reviews_url}")
                page.goto(reviews_url, timeout=60000)

                # 点击所有 “展开” 按钮，确保加载完整评论内容
                expand_buttons = page.locator('//*[contains (text (), "展开")]')
                button_count = expand_buttons.count()
                logging.info(f"找到 {button_count} 个 “展开” 按钮。")

                for i in range(button_count):
                    try:
                        expand_buttons.nth(i).click(timeout=5000)
                        time.sleep(1)  # 每次点击后等待 1 秒，确保内容加载
                    except Exception as e:
                        logging.error(f"点击第 {i + 1} 个展开按钮失败：{e}")
                        break   # 中断展开

                # 获取加载后的完整 HTML 内容
                reviews_content = page.content()
                browser.close()

                # 使用 lxml 解析评论内容
                reviews_tree = etree.HTML(reviews_content)
                reviews = reviews_tree.xpath('//div[contains(@id,"link-report")]/div//text()')
                reviews_cleaned = [' '.join(review.split()) for review in reviews if review.strip()]  # 清理空白内容
                return reviews_cleaned

            except Exception as e:
                logging.error(f"获取评论页面失败：{e}")
                browser.close()
                return []
    def parse_details(self, html_content, url):
        """
        解析电影详情页面，提取电影的基本信息
        这里示例提取标题、作者和评分，具体 XPath 根据实际页面结构调整
        """
        html_tree = etree.HTML(html_content)
        title_raw = html_tree.xpath("//h1//text()") # 书的标题
        title= [t.strip() for t in title_raw if t.strip()]  # 去除空白和换行符
        book_info_raw = html_tree.xpath('string(//*[@id="info"])') # 书的信息
        book_info = ' '.join(book_info_raw.split())  # 去除多余换行、空格，将内容合并为一行
        rating = html_tree.xpath('//*[@id="interest_sectl"]/div/div[2]/strong/text()') #评分
        # imgs = html_tree.xpath('//div[@id="mainpic"]//img/@src')
        content= html_tree.xpath('//*[@id="link-report-intra"]/span[1]')


        reviews_url=url+'reviews'
        reviews = self.fetch_reviews(reviews_url)

        # # 下载图片
        # img_path = None
        # if imgs:
        #     img_url = imgs[0]
        #     img_name = f"{title[0].strip() if title else 'unknown'}_{int(time.time())}"  # 确保文件名唯一
        #     img_path = self.save_image(img_url, img_name)

        detail = {

            "title": title[0].strip() if title else "未知标题",
            "book_info": book_info,  # 书籍的基本信息
            "rating": rating[0].strip() if rating else "无评分",
            "content": content if content else "无",
            "reviews": reviews,  # 评论内容
            "url":url
        }
        return detail

    def save_image(self, image_url, img_name):
        """下载图片并保存到本地"""
        try:
            # 如果 image_url 中不包含扩展名，则默认使用 .jpg
            if not image_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                ext = '.jpg'
            else:
                ext = os.path.splitext(image_url)[1]  # 获取扩展名

            # 清理文件名中的空格或斜杠
            img_name = img_name.replace(' ', '').replace('/', '_') + ext
            img_path = os.path.join(IMAGE_SAVE_PATH, img_name)

            # 下载图片
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                logging.info(f"图片 {img_name} 下载成功！")
                return img_path
            else:
                logging.error(f"图片下载失败，状态码：{response.status_code}")
                return None
        except Exception as e:
            logging.error(f"图片 {img_name} 下载失败：{e}")
            return None

    def save_to_mongo(self, data):
        """将数据保存到 MongoDB 数据库中"""
        try:
            # 检查是否已存在相同 URL 的数据
            if not self.collection.find_one({"url": data["url"]}):
                self.collection.insert_one(data)
                logging.info(f"成功保存：{data.get('title', '无标题')} 到 MongoDB")
            else:
                logging.info(f"数据已存在，跳过保存：{data.get('title', '无标题')}")
        except Exception as e:
            logging.error(f"保存到 MongoDB 失败：{e}")

    def save_to_csv(self):
        """将电影详细信息保存到 CSV 文件"""
        if not self.book_details:
            logging.warning("没有电影详细信息，无法保存到 CSV。")
            return

        df = pd.DataFrame(self.book_details)
        df.to_csv(self.output_csv, index=False, encoding='utf-8-sig')
        logging.info(f"所有电影详细信息已保存到 {self.output_csv}")

    def run(self):
        """主流程：依次爬取每个电影链接，提取详细信息，并保存到 MongoDB"""
        for url in self.book_urls:
            if self.collection.find_one({"url": url}):
                logging.info(f"URL 已存在于 MongoDB 中，跳过：{url}")
                continue
            html_content = self.fetch_page_content(url)
            if html_content:
                detail = self.parse_details(html_content, url)
                # print(detail)
                # exit()
                self.book_details.append(detail)
                self.save_to_mongo(detail)
            time.sleep(random.uniform(2, 5))  # 随机延时，避免被封禁
        logging.info(f"共提取到 {len(self.book_details)} 本电影的详细信息。")
        self.save_to_csv()
        for detail in self.book_details:
            logging.info(detail)

if __name__ == "__main__":
    # base_url = "https://search.douban.com/movie/subject_search?search_text=宝可梦&cat=1002"
    # scraper = DoubanScraper(base_url=base_url, max_pages=8)
    # scraper.run()
    # MongoDB 配置
    MONGO_URI = "mongodb://localhost:27017/"
    MONGO_DB = "pokemon_database"  # 数据库
    MONGO_COLLECTION = "douban_movie"  # 集合名称
    scraper = MovieDetailsScraper(input_file="urls.txt")
    scraper.run()
