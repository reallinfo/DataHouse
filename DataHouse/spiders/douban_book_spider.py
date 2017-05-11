import os
import urllib.parse

import pandas as pd
import scrapy
from scrapy.selector import Selector
from scrapy.http import HtmlResponse

from DataHouse.items import DoubanBook

douban_book_list = []


class DoubanBookSpider(scrapy.Spider):
    name = "doubanBook"

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch, br',
        'Host': 'book.douban.com',
        'Referer': 'https://book.douban.com/tag',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) '
                      'Version/9.0 Mobile/13B143 Safari/601.1 '
    }

    def start_requests(self):
        def get_tags_and_num():
            my_dict = {}
            import requests
            from bs4 import BeautifulSoup
            headers = {
                'Host': 'book.douban.com',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            }
            response = requests.get('https://book.douban.com/tag/', headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html5lib')
                for td in soup.find_all('div', class_='article')[0].find_all('td'):
                    my_dict[td.a.get_text().strip()] = int(td.b.get_text().replace('(', '').replace(')', ''))
            else:
                raise ValueError('Fail to get tags...')

            return my_dict

        # tags_and_num = get_tags_and_num()
        tags_and_num = {'算法': 43818}
        for tag, num in tags_and_num.items():
            urls = ['https://book.douban.com/tag/' + urllib.parse.quote(tag) + '?start=%d&type=T' % i for i in
                    range(0, num, 20)]
            for url in urls:
                yield scrapy.Request(url=url, callback=self.parse, headers=self.headers)

    def parse(self, response):
        for each_book in response.xpath('//li[@class="subject-item"]'):
            url = each_book.xpath('div[@class="pic"]/a[@class="nbg"]/@href').extract_first()
            title = each_book.xpath('div[@class="info"]/h2/a/@title').extract_first()
            image = each_book.xpath('div[@class="pic"]/a[@class="nbg"]/img/@src').extract_first()
            category = urllib.parse.unquote(response.url.split('?')[0].split('/')[-1])
            price = each_book.xpath('div[@class="info"]/div[@class="pub"]/text()').extract_first().split('/')[
                -1].strip()
            publishDate = each_book.xpath('div[@class="info"]/div[@class="pub"]/text()').extract_first().split('/')[
                -2].strip()
            publisher = each_book.xpath('div[@class="info"]/div[@class="pub"]/text()').extract_first().split('/')[
                -3].strip()
            score = each_book.xpath(
                'div[@class="info"]/div[@class="star clearfix"]/span[@class="rating_nums"]/text()').extract_first()
            scorerNum = each_book.xpath(
                'div[@class="info"]/div[@class="star clearfix"]/span[@class="pl"]/text()').extract_first().replace('(',
                                                                                                                   '').replace(
                '人评价)', '')

            douban_book = DoubanBook(title=title, url=url, image=image, category=category, score=score,
                                     scorerNum=scorerNum, price=price,
                                     publishDate=publishDate, publisher=publisher)
            douban_book_list.append(douban_book)

    def close(spider, reason):
        df = pd.DataFrame(douban_book_list)
        mkdirs_if_not_exists('./DataSet/douban/')
        df.to_excel('./DataSet/douban/book/算法.xlsx', sheet_name='Books')


def mkdirs_if_not_exists(dir_):
    if not os.path.exists(dir_) or not os.path.isdir(dir_):
        os.makedirs(dir_)
