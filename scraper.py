import re, requests, cbor, pickle, time
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from utils import  normalize
from tokenize_words import tokenize_content, token_frequencies, write_to_file, check_url_ascii, tokenize_url
from simhasing import sim_hash, compute_sim_hash_similarity

valid_domains = [r"^((.*\.)*ics\.uci\.edu)$", r"^((.*\.)*cs\.uci\.edu)$",
                r"^((.*\.)*informatics\.uci\.edu)$", r"^((.*\.)*stat\.uci\.edu)$"]

traps = r"^.*\/commit.*$|^.*\/commits.*$|^.*\/tree.*$|^.*\/blob.*"

valid_set = set()
visited_set = set()
content_hashes = set() 
content = dict()
content_file = dict()
ics_subdomains = dict()
global_frequencies = dict()
url_hashes = set()

def scraper(url, resp):
    """Scrap URL links seen on current page.
    
    Parameters
    ----------
    url : str
        a path to the website we will scrap from
    resp : dict
        a dict storing information about the website in the format of dict[str, str | int | Any]
    
    Returns
    -------
    list
        a list of websites to be scraped in the future
    """
    from pickle_storing import pickle_data

    if url in visited_set: # if URL has already been seen, we don't want to scrape information
        return []
    # since the URL is new, we tokenize and sim hash it
    visited_set.add(url)
    url_tokens = tokenize_url(url)
    url_freq = token_frequencies(url_tokens)
    url_hash = sim_hash(url_freq)

    try:
        # check the status of the webpage and if content is not None
        if (resp.status == 200 and resp.raw_response and resp.raw_response.content):
            if len(resp.raw_response.content) > 2000000: # if contents of the page are too large, we save URL but don't scrape
                valid_set.add(url)
                ics_subdomain(url)
                
                pickle_data(get_crawl_data(), "current_crawl_data.pickle")
                save_data()
                
                return []
            
            tokens = tokenize_content(resp.raw_response.content) # get tokens
            frequencies = token_frequencies(tokens) # compute token frequencies
            hash_vector = sim_hash(frequencies) # compute the hash for the content
            total_tokens = len(tokens) # count of total tokens
            
            valid_set.add(url)
            ics_subdomain(url)
            content[url] = total_tokens # [content folder num, total tokens]
            
            if total_tokens < 100 or total_tokens > 60000: # if the tokens from page are too small or too large, we save URL info but dont check content similarity
                pickle_data(get_crawl_data(), "current_crawl_data.pickle")
                save_data()
                
                return []
            
            if check_content(hash_vector, similarity_threshold=59): # content unique get links
                url_hashes.add(url_hash)
                add_token_to_frequencies(tokens)
                content_hashes.add(hash_vector)
                links = extract_next_links(url, resp) # extract the links
                
                pickle_data(get_crawl_data(), "current_crawl_data.pickle")
                save_data()
                
                return links
            else: # content not unique do not get links
                # path_threshold_update(url)
                pickle_data(get_crawl_data(), "current_crawl_data.pickle")
                save_data()

                return []
        elif resp.status in set([301, 302, 308, 309]) and resp.raw_response and resp.url: # if the URL status is one from the set, we save redirected URL info
            location = resp.url
            redirected_url = create_absolute_url(url, location)
            if  redirected_url not in visited_set and is_valid(redirected_url):
                valid_set.add(url)
                ics_subdomain(url)
                
                pickle_data(get_crawl_data(), "current_crawl_data.pickle")
                save_data()

                return [redirected_url]
            else:
                pickle_data(get_crawl_data(), "current_crawl_data.pickle")
                save_data()
                
                return []
        else:
            pickle_data(get_crawl_data(), "current_crawl_data.pickle")
            save_data()
            
            return []
    except:
        pickle_data(get_crawl_data(), "current_crawl_data.pickle")
        save_data()
        
        return []

# This function needs to return a list of urls that are scraped from the response. 
# (An empty list for responses that are empty). These urls will be added to the Frontier 
# and retrieved from the cache. These urls have to be filtered so that urls that do not 
# have to be downloaded are not added to the frontier.

def extract_next_links(url, resp) -> list:
    """Extract links (or URLs) from the current webpage.

    Parameters
    ----------
    url : str
        the path of the current webpage
    resp : dict
        a dict storing information about the website in the format of dict[str, str | int | Any]

    Returns
    -------
    list
        a list of links found on the current webpage 
    """
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    text = resp.raw_response.content
    new_urls  = set()
    soup = BeautifulSoup(text, "html.parser") # gets HTML content from text (byte string)
    for tag in soup.find_all('a', href=True):
        if tag.get('href'):
            new_url = tag['href']
            absolute_url = create_absolute_url(url, new_url) # create an absolute URL that we check against our visited set & new URLs set
            if absolute_url not in visited_set and absolute_url not in new_urls and is_valid(absolute_url):
                # tokenize and compute sim hash for the absolute URL
                new_url_tokens = tokenize_url(absolute_url)
                new_url_freq = token_frequencies(new_url_tokens)
                new_url_hash = sim_hash(new_url_freq)
                # check if the URL is similar to previous URLs seen
                if check_url(new_url_hash, similarity_threshold=59):
                    # since its similar, we then add it to new_urls set
                    new_urls.add(absolute_url)  
                else:
                    # since its NOT similar, we add it to our visited and valid set to not be tokenized & sim hashed again
                    visited_set.add(absolute_url) 
                    valid_set.add(absolute_url)
            else:
                visited_set.add(absolute_url)
    return list(new_urls)
    
def create_absolute_url(base_url, new_url):
    """Create the absolute URL based on the base URL and the new URL passed in.
    
    Parameters
    ----------
    base_url : str
        a URL of the current webpage
    new_url : str
        a newly created URL from links found on the current URL page
    
    Returns
    -------
    str
        a str of the absolute URL
    """
    new_url = new_url.split('#', 1)[0].strip().lower()
    absolute_url = urljoin(base_url, new_url)
    absolute_url = normalize(absolute_url)
    return absolute_url
    
# def path_threshold_check(url, threshold = 10):
#     base_url = url.split('?', 1)[0].strip()
    
#     if base_url in url_path_count and url_path_count[base_url] >= threshold:
#         return False
        
#     return True

# def path_threshold_update(url)
#     base_url = url.split('?', 1)[0].strip()

#     if base_url not in url_path_count:
#         url_path_count[base_url] = 1
#     else:
#         url_path_count[base_url] += 1

def ics_subdomain(url):
    """Check if the URL is part of the valid ics links.

    Parameters
    ----------
    url : str
        the URL to be checked against the valid ics subdomains
    """
    # check if the url path exists and increment accordingly, otherwise add path to ics_subdomains with count of 1
    parsed = urlparse(url)
    if (re.match(valid_domains[0], parsed.netloc)):
        path = f"{parsed.netloc}"
        if path in ics_subdomains:
            ics_subdomains[path] += 1
        else:
            ics_subdomains[path] = 1


def is_valid(url) -> bool:
    """Check if the URL is valid against the acceptable set of URL's.

    Parameters
    ----------
    url : str
        a URL that is checked for validity

    Returns
    -------
    bool
        a bool that indicates if the URL is valid
    """
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
        
        if not check_url_ascii(url):
            return False

        if check_for_repeating_dirs(url) or check_for_traps(url):
            return False
        
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|mpg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|war|img|apk|ff"
            + r"|thmx|mso|arff|rtf|jar|csv|bib|java|m|cc|odp|class|mexglx"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|pov|sh)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise


def check_url(new_hash_vector, similarity_threshold = 64):
    """Check if the new content set is exact or approximately similar to existing sets.
    
    Parameters
    ----------
    new_hash_vector : tuple
        a tuple containing the hash of a URL's tokens
    similarity_threshold : int
        an arbitrary value set to 64 for a similarity score threshold

    Return
    ------
    bool
        a bool indicating how similar the content is to the threshold\n
        (Very Similar = False, Not Similar = True)
    """

    # Check for exact match first
    if new_hash_vector in url_hashes:
        return False  # Exact match found, content is not unique

    # Check for approximate similarity
    for hash_vector in url_hashes:
        if compute_sim_hash_similarity(new_hash_vector, hash_vector) > similarity_threshold:
            return False  # Similar content found, content is not unique

    return True  # Content is unique

def check_content(new_hash_vector, similarity_threshold = 64):
    """Check if the new content set is exact or approximately similar to existing sets.
    
    Parameters
    ----------
    new_hash_vector : tuple
        a tuple containing the hash of a URL's tokens
    similarity_threshold : int
        an arbitrary value set to 64 for a similarity score threshold

    Return
    ------
    bool
        a bool indicating how similar the content is to the threshold\n
        (Very Similar = False, Not Similar = True)
    """

    # Check for exact match first
    if new_hash_vector in content_hashes:
        return False  # Exact match found, content is not unique

    # Check for approximate similarity
    for hash_vector in content_hashes:
        if compute_sim_hash_similarity(new_hash_vector, hash_vector) > similarity_threshold:
            return False  # Similar content found, content is not unique

    return True  # Content is unique

def save_data():
    """Saves the current state of crawled information."""
    num_pages = len(valid_set)
    longest_page = max(content, key=content.get) if content else "None"
    top_50 = sorted(global_frequencies.items(), key=lambda x: (x[0])) # sort in alphabetical order
    top_50 = sorted(top_50, key=lambda x: (x[1]), reverse=True) [:50]
    statistics = {"Unique Pages":num_pages, "Longest Page":longest_page, "Top 50":top_50, "ICS domain":sorted(ics_subdomains.items(), key=lambda x: (x[0]))}
    with open('data_statistics.txt', 'w') as file:
        # Write the statistics data to the file
        for key, value in statistics.items():
            file.write(f"{key}: {value}\n")
    with open('data_valid_urls.txt', 'w') as file:
        # Write the statistics data to the file
        for i, url in enumerate(valid_set):
            file.write(f"{i}: {url}\n")
    with open('data_visisted_urls.txt', 'w') as file:
        # Write the statistics data to the file
        for i, url in enumerate(visited_set):
            file.write(f"{i}: {url}\n")
    with open('data_frequencies.txt', 'w') as file:
        # Write the statistics data to the file
        for k, v in global_frequencies.items():
            file.write(f"{k}: {v}\n")
    with open('data_content.txt', 'w') as file:
        # Write the statistics data to the file
        for k, v in content.items():
            file.write(f"{k}: {v}\n")
    with open('file_numbers.txt', 'w') as file:
        # Write the statistics data to the file
        for k, v in content_file.items():
            file.write(f"{k}: {v}\n")
    with open('data_ics_domains.txt', 'w') as file:
        # Write the statistics data to the file
        for k, v in sorted(ics_subdomains.items(), key=lambda x: (x[0])):
            file.write(f"{k}: {v}\n")

def add_token_to_frequencies(tokens):
    """Adds tokens of a list to the global token frequency count.
    
    Parameters
    ----------
    tokens : list
        a list of tokens
    """
    for token in tokens:
        if token in global_frequencies:
            global_frequencies[token] += 1
        else:
            global_frequencies[token] = 1
    

def check_for_repeating_dirs(url) -> bool:
    """Check for the repeating directory trap.

    Parameters
    ----------
    url : str
        a URL to the current webpage to be checked

    Returns
    -------
    bool
        a bool indicating if the URL contains repeated directories
    """
    pattern = r"^.*?(/.+?/).*?\1.*$|^.*?/(.+?/)\2.*$"
    if re.match(pattern, url):
        return True
    return False

def check_for_traps(url) -> bool:
    """Validates the URL's path composition against a regex statement.

    Parameters
    ----------
    url : str
        a URL to the current webpage to be checked

    Returns
    -------
    bool
        a bool indicating if the URL contains simple traps
    """
    if re.match(traps, url):
        return True
    return False

def get_crawl_data():
    """Fetch crawled data information.

    Returns
    -------
    dict
        a dict of all the web crawling information containers
    """
    crawl_data = {
        "valid_urls": valid_set, 
        "visited_urls": visited_set, 
        "content_hashes": content_hashes, 
        "content": content,
        "content_file": content_file,
        "ics_subdomains": ics_subdomains,
        "global_frequencies": global_frequencies,
        "url_hashes": url_hashes
    }
    return crawl_data

if __name__ == "__main__":
    # testing is_valid function

    # url = "https://spaces.lib.uci.edu/reserve/Science"
    # # flag, disallows = check_robot_permission(url)
    
    # # print(extract_next_links(url, url, disallows))

    # # print(disallows)
    # print(is_ics_subdomain("https://archive.ics.uci.edu/path/path/path/"))
    # # # Testing retrieving tokens from a webpage
    # response = requests.get(url)
    # soup = BeautifulSoup(response.text, "html.parser")
    # # soup = BeautifulSoup(response.raw_response.content, "html.parser")
    # # text_tags = soup.find_all(['p','h1','h2','h3','h4','h5','h6','li','ul'])
    # text_tags = soup.find_all(['p','h1','h2','h3','h4','h5','h6','li','ul'])
    # # [print(tag.get_text()) for tag in text_tags]
    # text_content = [tag.get_text(separator = " ", strip = True) for tag in text_tags]
    # print(text_content)
    # # text = ' '.join(text_content)

    # # print(text_content)
    # # # Downloading the file since the text is now too large to pass in
    # # with open('webpage_text.txt', 'w', encoding='utf-8') as file:
    # #     file.write(text_content)
    # # Testing the tokenize function with the downloaded page as a text file
    # # print(tokenize("webpage_text.txt"))

    # # === Testing the lengths of lists being returned from a line-by-line read
    # my_list = tokenize(text_content)
    # print(my_list)
    # print(len(my_list))
    # my_list1 = tokenize("webpage_text.txt")
    # print(len(my_list1))

    # # Testing similar tokens in the two "my_lists"
    # count = count_common_tokens(set(my_list),set(my_list1))
    # print(count)


    # Testing crawl delay function
    # with open("/Users/shika/Downloads/stacks2robots.txt", 'r') as f:
    #     print("Crawl Delay is:", parse_robots_txt_for_crawl_delay(f))

    # Testing gathering sitemaps
    # with open("/Users/shika/Downloads/robots.txt", 'r') as txt_file:
    #     print("List of sitemaps:",len(find_all_sitemaps(txt_file)))

        # check for traps 
            # algorithm for similarity


    # my_url = "https://www.google.com/"
    papa_url = "https://ics.uci.edu/~mikes/"
    print(is_valid("http://swiki.ics.uci.edu/doku.php/start?ns=courses&tab_files=files&do=media&tab_details=history&image=projects%3Anotice_power_shutdown_rev_0422021.png"))
    print(normalize(papa_url))
    num_pages = len(valid_set)
    longest_page = max(content, key=content.get) if content else "None"
    top_50 = sorted(global_frequencies.items(), key=lambda x: (x[0])) # sort in alphabetical order
    top_50 = sorted(top_50, key=lambda x: (x[1]), reverse=True) [:50]
    l = {"b":1, "a": 2, "d": 3, "c": 4}
    statistics = {"Unique Pages":num_pages, "Longest Page":longest_page, "Top 50":top_50, "ICS domain":sorted(l.items(), key=lambda x: (x[0]))}
    
    print(statistics)
    url_tokens = tokenize_url(papa_url)
    print(url_tokens)
    url_freq = token_frequencies(url_tokens)
    print(url_freq)
    url_hash = sim_hash(url_freq)
    print(url_hash)
    save_data()
    # test1 = "https://www.ics.uci.edu/community/news/view_news.php?id=2"
    # test2 = "https://www.ics.uci.edu/community/news/view_news.php?id=2227"

    # url_token = tokenize_url(test1)
    # papa_token = tokenize_url(test2)

    # url_hash = sim_hash(url_token)
    # papa_hash = sim_hash(papa_token)

    # print(compute_sim_hash_similarity(url_hash, papa_hash))

    # resp = requests.get("https://google.com")
    # print(type(resp))