from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time
from pickle_storing import load_pickled_data, crawl_data


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):
        try:
            crawl_data = load_pickled_data("current_crawl_data.pickle")
            if crawl_data:
                print("loading past pickled data")
                print(crawl_data["url_hashes"])
                print("done loading with pickled data")
            else:
                print("No pickled data found. Starting fresh crawl.")
        except (KeyError, FileNotFoundError) as err:
            print(f"Error loading pickled data: {err}")
        while True:
            # post
            tbd_url = self.frontier.get_tbd_url()
            # wait
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            try:
                resp = download(tbd_url, self.config, self.logger)
            except:
                pass # remove this and test a reconnection and load of the data we already have in crawl_data
                # call function to retry repeatedly?

            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
