
import scrapy
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
import json
import requests

class LinksTextSpider(scrapy.Spider):
    name = 'link-spider'

    def __init__(self, *args, **kwargs):
            super(LinksTextSpider, self).__init__(*args, **kwargs)
            # url = kwargs.get('url')
            # if not url:
            #     raise ValueError("No URL given")
            self.start_urls = ['https://linktr.ee/basivibe', 'https://linktr.ee/HonorHouse','https://linktr.ee/ftntwitter', 'https://linktr.ee/georgejohnsons']
            self.headers = {"origin": "https://linktr.ee","referer": "https://linktr.ee"}
            self.apiurl = "https://linktr.ee/api/profiles/validation/gates"

        
    def start_requests(self):
        for url in self.start_urls:
            account_name = url.split('/')[-1]
            cookies={'accepted_content_warnings':f'["{account_name}"]'}
            yield scrapy.Request(url=url,headers=self.headers , cookies=cookies,callback=self.parse)        


    def get_result(self, response, user_info):
        boxes = response.css('.sc-bdfBwQ.pkAuV')
        list_text = [b.css('p::text').get() for b in boxes]
        list_link = [self.get_link(b, user_info) for b in boxes]
        list_link_sets = [ {'link':list_link[i], 'text':list_text[i]} for i in range(len(list_link))]
        result = {
            "resolved_url": response.url,
            "Items" : list_link_sets
        }
        return result

    def get_link(self, b, user_info):
        try:
            link = b.css('a::attr(href)').extract()[0]
        except:
            link_title = b.css('p::text').get()
            account_id = user_info['account_id']
            li_sense_post_id = user_info['dict_post'][link_title]
            apidata = {"accountId":account_id,
                    "validationInput":{"acceptedSensitiveContent":li_sense_post_id},
                        "requestSource":{"referrer":None}}
            res = requests.post(url = self.apiurl, headers = self.headers, json = apidata)
            api_data = json.loads(res.text)
            link = api_data['links'][0]['url']
        return link

    def parse(self, response):
        try:
            h1 = response.css('h1::text').get()
        except Exception as e:
            print('h1 error:', str(e))
            h1 = ''
        if h1 == 'Sensitive Content':
            print('*** Sensitive Content ***, cookie is not working')
            result = self.get_result(response, True)
        else:
            j_NEXT_DATA = response.css('#__NEXT_DATA__::text').get()
            j_data = json.loads(j_NEXT_DATA)
            account_id = j_data['props']['pageProps']['account']['id']
            links = j_data['props']['pageProps']['account']['links']

            dict_post = dict()
            for ele in links:
                if ele['rules']['gate']['activeOrder'] == ['sensitiveContent']:
                        dict_post[ele['title']]=ele['id']

            user_info = {'account_id':account_id, 'dict_post':dict_post}
            result = self.get_result(response, user_info)
        yield result
