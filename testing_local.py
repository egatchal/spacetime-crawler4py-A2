from collections import deque
import scraper
import time
from pickle_storing import load_pickled_data
import scraper
import requests
import cbor
import time

from utils.response import Response

frontier = deque()
# frontier.append("https://www.stat.uci.edu")
# frontier.append("https://www.informatics.uci.edu")
frontier.append("https://archive.ics.uci.edu")
# frontier.append("https://www.gutenberg.org")
# frontier.append("https://wiki.ics.uci.edu/doku.php/announce:announce-2022")
class Response(object):
    def __init__(self, url, resp):
        self.url = url
        self.status = resp.status_code
        self.error = resp.reason
        try:
            self.raw_response = resp
        except TypeError:
            self.raw_response = None
            
def download(url):
    resp = requests.get(url)
    print(resp)
    if hasattr(resp, "status_code"):
        print(f"Downloaded {url}, status <{resp.status_code}>.")
    else:
        print(f"Downloaded {url}, status <{404}>.")
        return Response(url, {
        "error": f"Spacetime Response error {resp} with url {url}.",
        "status": 404,
        "url": url})
    try:
        if resp and resp.content:
            return Response(url, resp)
    except (EOFError, ValueError) as e:
        pass
    return Response(url, {
        "error": f"Spacetime Response error {resp} with url {url}.",
        "status": 404,
        "url": url})

def run(restart):
        if not restart:
            crawl_data = load_pickled_data("current_crawl_data.pickle")
            print(crawl_data)
            if crawl_data:
                print("Data has been uploaded from previous crawl.")
            else:
                print("No pickled data found. Starting fresh crawl.")
        while len(frontier):
            tbd_url = frontier.popleft()
            resp = download(tbd_url)
            scraped_urls = scraper.scraper(tbd_url, resp)
            for scraped_url in scraped_urls:
                frontier.append(scraped_url)
            time.sleep(0.5)
        print("Frontier is empty. Stopping Crawler.")

if __name__ == "__main__":
    # testing is_valid function
    run(False)