from playwright.sync_api import sync_playwright
from lxml import etree
import time
import requests
from pymongo import MongoClient
import logging
class DoubanScraper:
    def __init__(self, base_url,max_pages=5,output_file="urls.txt"):
        """
        初始化 DoubanScraper 类
        :param base_url: 豆瓣基础搜索 URL
        :param max_pages: 爬取的最大分页数
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.all_urls = []  # 用于存储所有爬取到的图书链接
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
        解析网页内容，提取图书链接
        :param html_content: 网页 HTML 内容
        :return: 提取到的图书链接列表
        """
        html_tree = etree.HTML(html_content)
        book_urls = html_tree.xpath('//*[@id="root"]//div/div/div/div[1]/a/@href')
        unique_urls = list(set(book_urls))  # 去重
        return unique_urls

    def save_urls_to_file(self):
        """ 将所有图书链接保存到本地 txt 文件 """
        with open(self.output_file, "w", encoding="utf-8") as file:
            for url in self.all_urls:
                file.write(url + "\n")
        print(f"所有图书链接已保存到 {self.output_file}")
    def run(self):
        """
        主流程，依次爬取分页 URL，提取并存储图书链接
        """
        root_urls = self.get_root_urls()
        for url in root_urls:
            html_content = self.fetch_page_content(url)
            if html_content:
                page_urls = self.parse_urls(html_content)
                self.all_urls.extend(page_urls)
                print(f"解析到 {len(page_urls)} 个图书链接。")
            time.sleep(5)  # 避免频繁请求被封禁

        # 去重并输出所有链接
        self.all_urls = list(set(self.all_urls))
        print(f"共解析到 {len(self.all_urls)} 个唯一图书链接。")
        self.save_urls_to_file()



# MongoDB 配置
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "pokemon_database"          # 数据库
MONGO_COLLECTION = "douban_collection"   # 集合名称

class BookDetailsScraper:
    def __init__(self, input_file="urls.txt"):
        """
        初始化 BookDetailsScraper 类
        :param input_file: 存储图书链接的文件名
        """
        self.input_file = input_file
        self.book_urls = self.load_urls_from_file()
        self.book_details = []  # 存储图书详细信息

        # 初始化 MongoDB 连接
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB]
        self.collection = self.db[MONGO_COLLECTION]

    def load_urls_from_file(self):
        """从本地 txt 文件中读取图书链接"""
        try:
            with open(self.input_file, "r", encoding="utf-8") as file:
                urls = [line.strip() for line in file if line.strip()]
            print(f"从 {self.input_file} 读取到 {len(urls)} 个图书链接。")
            return urls
        except Exception as e:
            print(f"读取 {self.input_file} 文件失败：{e}")
            return []

    def fetch_page_content(self, url):
        """使用 Playwright 爬取单个图书详情页面的内容"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                print(f"正在爬取图书详情：{url}")
                page.goto(url, timeout=60000)
                page.wait_for_selector("body", state="attached", timeout=15000)  # 等待页面的 <body> 加载完成
                content = page.content()
                # print(content)
                # exit()
                browser.close()
                return content
            except Exception as e:
                print(f"获取图书详情页面失败：{e}")
                browser.close()
                return None

    def parse_details(self, html_content, url):
        """
        解析图书详情页面，提取图书的基本信息
        这里示例提取标题、作者和评分，具体 XPath 根据实际页面结构调整
        """
        html_tree = etree.HTML(html_content)
        title = html_tree.xpath("//h1//text()")
        author = html_tree.xpath('//div[@id="info"]/span[1]/a/text()')
        rating = html_tree.xpath('//strong[@class="ll rating_num"]/text()')
        detail = {
            "url": url,
            "title": title[0].strip() if title else "未知标题",
            "author": author[0].strip() if author else "未知作者",
            "rating": rating[0].strip() if rating else "无评分"
        }
        return detail
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
            print(f"成功保存：{data.get('title', '无标题')} 到 MongoDB")
        except Exception as e:
            print(f"保存到 MongoDB 失败：{e}")

    def run(self):
        """主流程：依次爬取每个图书链接，提取详细信息，并保存到 MongoDB"""
        for url in self.book_urls:
            html_content = self.fetch_page_content(url)
            if html_content:
                detail = self.parse_details(html_content, url)
                self.book_details.append(detail)
                self.save_to_mongo(detail)
            time.sleep(2)
        print(f"共提取到 {len(self.book_details)} 本图书的详细信息。")
        for detail in self.book_details:
            print(detail)


if __name__ == "__main__":
    # base_url = "https://search.douban.com/book/subject_search?search_text=宝可梦&cat=1001"
    # scraper = DoubanScraper(base_url=base_url, max_pages=6)
    # scraper.run()
    scraper = BookDetailsScraper(input_file="urls.txt")
    scraper.run()
