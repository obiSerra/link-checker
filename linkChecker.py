
# -*- coding: utf-8 -*-
import scrapy, csv, re
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy import signals
from sys import exit
from yaml import load

usage = "$ scrapy runspider linkChecker.py -a outputfile=<filename>.csv"

##################################################################
#
# Usage: $ scrapy runspider linkChecker.py -a outputfile=<filename>.csv
#
##################################################################
class LinkCheckerSpider(CrawlSpider):
    name = 'linkChecker'

    def __init__(self, outputfile = ""):
       
        f = open('config.yaml', 'r')
        config = load(f)
        f.close()        
        if "allowed_domains" not in config:
            exit("[!] Missing 'allowed_domains' from config")
        if "start_urls" not in config:
            exit("[!] Missing 'start_urls' from config")
        if outputfile == "":
            exit("[!] USAGE: " + usage)

        if "handle_httpstatus_list" in config:
            self.handle_httpstatus_list = config["handle_httpstatus_list"]
        self.allowed_domains = config["allowed_domains"]
        self.start_urls = config["start_urls"]
        self.infile = open(outputfile,"w")
        self.writer = csv.writer(self.infile)
        headers = ["url","origin url", "link text", "status", "type"]
        self.writer.writerow(headers)


    def writeToCsv(self, cols):        
        self.writer.writerow(cols)
        
    def parse(self, response):
        url = response.url

        origin = ""
        text = ""
        
        if "origin-url"in response.meta:
            origin = response.meta['origin-url']
        if "link-text" in response.meta:
            text = response.meta['link-text']

        self.writeToCsv([response.url, origin, text, response.status, "html"])

        for next_page in response.css('a[href]'):
            content = next_page.xpath("text()").extract_first()
            identifier = ""
            if content != None:
                identifier = content.replace('\n', '').replace('\r', '')
                identifier = re.sub(r"\s\s+", " ", identifier).strip()

            if identifier == "" and hasattr(next_page.attrib, "class"):
                identifier = "." + re.sub(r"\s\s+", ".", next_page.attrib["class"])

            yield response.follow(next_page, self.parse, meta={
                'origin-url': url,
                'link-text': identifier
            })
                
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(LinkCheckerSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_error, signal=signals.spider_error)
        return spider

    def spider_error(self, failure, response):
        origin = ""
        text = ""
        if hasattr(response.meta, "origin-url"):
            origin = response.meta['origin-url']
        if hasattr(response.meta, "link-text"):
            text = response.meta['link-text']
        self.writeToCsv([response.url, origin, text, response.status, "file"])
