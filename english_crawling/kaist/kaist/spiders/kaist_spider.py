import scrapy
from kaist.items import KaistItem

class KaistSpider(scrapy.Spider):
    name = "kaist"

    def start_requests(self):
        base_url = 'https://www.nature.com/search?q=kaist&order=date_desc&page='
        for i in range(13):
            page_num = i+1
            url = base_url + str(page_num)
            yield scrapy.Request(url, self.parse, dont_filter = True)

    def parse(self, response):
        url_list = response.xpath('//*[@role="heading"]/a/@href').extract()
        for url in url_list:
            article_url = 'https://www.nature.com' + url
            yield scrapy.Request(article_url, self.parse_article, meta={'url' : article_url})
    
    def parse_article(self, response):

        item = KaistItem()
        
        article_url = response.meta['url']
        article_title = response.xpath('//*[@class="c-article-title"]/text()').extract()[0]
        article_data = ''.join(response.xpath('//*[@class="c-article-section__content"]/p/text()').extract())
        article_data = article_data.replace('\n', '')

        item['urls'] = article_url
        item['titles'] = article_title
        item['contents'] = article_data


        yield item