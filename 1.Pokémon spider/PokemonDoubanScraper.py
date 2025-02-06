import io
import sys
import random
import requests
import csv
import time
import logging
from lxml import etree
from pymongo import MongoClient

# 配置部分
API_URL = "https://api.xiaoxiangdaili.com/ip/get"
APP_KEY = '1204778417330212864'
APP_SECRET = 'TwU0IYaT'
PROXY_API_URL = "https://api.xiaoxiangdaili.com/ip/get"
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "pokemon_database"
MONGO_COLLECTION = "pokemon_collection"
# CSV_FILE_PATH = 'pokemon.csv'
IMAGE_SAVE_PATH = r'C:\Users\luke\Desktop\project'

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class PokemonDoubanScraper:
    def __init__(self):
        self.base_url = 'https://tw.portal-pokemon.com/play/pokedex/'
        self.pokemon_data = []
        self.data_list = []
        self.client = MongoClient(MONGO_URI)  # MongoDB 本地连接
        self.db = self.client[MONGO_DB]  # 创建/连接数据库
        self.collection = self.db[MONGO_COLLECTION]  # 创建/连接集合
        self.uapools = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.22 Safari/537.36 SE 2.X MetaSr 1.0',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)',
            'Mozilla/5.0 (compatible; ABrowse 0.4; Syllable)',
        ]

    def get_proxy(self):
        res = requests.get(PROXY_API_URL, params={'appKey': APP_KEY, 'appSecret': APP_SECRET, 'wt': 'text', 'cnt': 1})
        proxy = str(res.content, 'utf-8')
        logging.info(f"API response: {proxy}")
        return proxy

    def get_ip(self):
        proxy = self.get_proxy()
        proxy_meta = f"http://{APP_KEY}:{APP_SECRET}@{proxy}"
        proxies = {'http': proxy_meta, 'https': proxy_meta}
        return proxies

    def get_random_headers(self):
        random_user_agent = random.choice(self.uapools)
        headers = {"User-Agent": random_user_agent}
        return headers

    def get_pokemon_base_url(self):
        for i in range(1, 1011):  # Adjust range as needed
            formatted_number = str(i).zfill(4)
            url = f"{self.base_url}{formatted_number}"
            self.pokemon_data.append(url)

    def get_pokemon_base_urls_with_variations(self):
        pokemon_data_with_variations = []
        for url in self.pokemon_data:
            pokemon_data_with_variations.append(url)
            for j in range(1, 4):
                pokemon_data_with_variations.append(f"{url}_{j}")
        return pokemon_data_with_variations

    def get_html_content(self, url, headers, proxies):
        try:
            response = requests.get(url, headers=headers, proxies=proxies)
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            return None

    def save_image(self, save_path, img_name, image_url, headers, proxies):
        try:
            content = requests.get(image_url, headers=headers, proxies=proxies).content
            img_name = img_name.replace(' ', '') + image_url[-4:]
            with open(save_path + img_name, 'wb') as f:
                f.write(content)
            logging.info(f"Image {img_name} downloaded successfully.")
        except Exception as e:
            logging.error(f"Failed to save image: {e}")

    def save_to_mongo(self, pokemon_info):
        self.collection.insert_one(pokemon_info)
        logging.info(f"Saved {pokemon_info['name']} to MongoDB")
    #
    # def save_to_csv(self, data):
    #     with open(CSV_FILE_PATH, 'a', newline='', encoding='utf-8') as file:
    #         writer = csv.DictWriter(file, fieldnames=data.keys())
    #         if file.tell() == 0:  # If file is empty, write header
    #             writer.writeheader()
    #         writer.writerow(data)

    def parse_pokemon_data(self, html):
        try:
            html_tree = etree.HTML(html)
            data_item = {}
            elements_a = html_tree.xpath('/html/body/div[1]/div/div[2]/div/div[2]/p')
            if elements_a:
                data_item['编号'] = elements_a[0].xpath('.//text()')[0]
                data_item['姓名'] = elements_a[1].text + (elements_a[2].text if len(elements_a) > 3 else '')
                attributes = html_tree.xpath('/html/body/div[1]/div/div[3]/div/div[2]/div[2]/div/a/span')
                data_item['属性'] = ''.join([attr.text for attr in attributes])
                weaknesses = html_tree.xpath('/html/body/div[1]/div/div[3]/div/div[3]/div[2]/div/div/a/span')
                data_item['弱点'] = ''.join([weakness.text for weakness in weaknesses])
                data_item['数据'] = ''.join(html_tree.xpath('/html/body/div[1]/div/div[3]/div/div[4]//text()')).strip()
                img_url = 'https://tw.portal-pokemon.com' + \
                          html_tree.xpath('/html/body/div[1]/div/div[3]/div/div[1]/div/img[3]')[0].get("src")
                self.save_image(IMAGE_SAVE_PATH, data_item['编号'] + data_item['姓名'], img_url,
                                self.get_random_headers(), self.get_ip())
                data_item['imgs'] = img_url
                # self.save_to_csv(data_item)
                self.save_to_mongo(data_item)
            else:
                logging.warning("No valid data found.")
        except Exception as e:
            logging.error(f"Failed to parse HTML: {e}")

    def run(self):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')  # 设置IO流解决字符编码问题
        self.get_pokemon_base_url()
        pokemon_urls = self.get_pokemon_base_urls_with_variations()

        for i, url in enumerate(pokemon_urls):
            # Start from 4037 as an example
            # print(url)
            # exit()
            logging.info(f"Fetching data for Pokemon {i}...")
            headers = self.get_random_headers()
            proxies = self.get_ip()
            # print(url)
            # exit()
            html_content = self.get_html_content(url, headers, proxies)

            if html_content:
                self.parse_pokemon_data(html_content)
                time.sleep(15)  # Adjust sleep time as needed
                logging.info(f"Pokemon data parsed successfully.{url}")
            else:
                logging.error(f"Failed to fetch data for Pokemon {url}")


if __name__ == '__main__':
    scraper = PokemonDoubanScraper()
    scraper.run()
