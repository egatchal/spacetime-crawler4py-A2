import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
valid_domains = [r".*\.*ics\.uci\.edu", r".*\.*cs\.uci\.edu",
                r".*\.*informatics\.uci\.edu", r".*\.*stat\.uci\.edu"]
valid_urls = set()
invalid_urls = set()
tokens = dict()

def scraper(url, resp):
    # robot.txt check goes here
    
    if not is_valid(url): # check if the url is valid
        invalid_urls.add(url)
        return []

    if url in valid_urls or url in invalid_urls: # already searched through that url (skip)
        return []
    
    # frunction - "tokenize" extract all tokens here (exclude urls)

    links = extract_next_links(url, resp)
    
    return [link for link in links if is_valid(link)]

# This function needs to return a list of urls that are scraped from the response. 
# (An empty list for responses that are empty). These urls will be added to the Frontier 
# and retrieved from the cache. These urls have to be filtered so that urls that do not 
# have to be downloaded are not added to the frontier.

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    if resp.status == 200 and resp.raw_response.content:
        soup = BeautifulSoup(resp.raw_response.content, "html.parser")
        links  = [link.get('href') for link in soup.find_all('a', href=True)]
        return links
    return list()

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
       
        if parsed.scheme not in set(["http", "https"]):
            return False

        if  not (re.match(valid_domains[0], parsed.netloc) or \
            re.match(valid_domains[1], parsed.netloc) or \
            re.match(valid_domains[2], parsed.netloc) or \
            re.match(valid_domains[3], parsed.netloc)): # check for valid domain
                return False
        
        # check for repetition within the path

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

if __name__ == "__main__":
    # testing is_valid function
    print(is_valid("https://archive.ics.uci.edu/"))
    print(is_valid("https://ics.uci.edu/"))
    print(is_valid("https://youtube.com/"))
