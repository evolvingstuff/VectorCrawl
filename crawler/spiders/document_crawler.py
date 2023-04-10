import scrapy
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin


class DocumentSpider(scrapy.Spider):
    name = 'document_spider'
    custom_settings = {
        'DEPTH_LIMIT': 3  # Set a limit to the depth of the crawl (optional)
    }

    def __init__(self, start_url, progress_callback, *args, **kwargs):
        super(DocumentSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url]
        self.progress_callback = progress_callback
        self.allowed_domain = urlparse(start_url).netloc
        self.start_path = urlparse(start_url).path
        self.extracted_texts = []

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        yield from self.parse_text(response)

    def parse_text(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script and style elements
        for element in soup(['script', 'style']):
            element.extract()

        # Extract text and remove extra whitespace
        text = soup.get_text()
        text = ' '.join(text.split())

        self.extracted_texts.append(text)

        self.progress_callback(msg=f'{len(self.extracted_texts)} extracted texts')

        # Find and follow other links
        for link in soup.find_all('a', href=True):
            next_url = link['href']
            next_url = urljoin(response.url, next_url)

            # Check if the link is within the same portion of the website
            if (urlparse(next_url).netloc == self.allowed_domain and
                    urlparse(next_url).path.startswith(self.start_path)):
                yield scrapy.Request(next_url, callback=self.parse_text)