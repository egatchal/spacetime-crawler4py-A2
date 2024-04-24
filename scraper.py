import re, requests, cbor, pickle, time
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from utils import  normalize
from tokenize_words import tokenize_content, token_frequencies, write_to_file, check_file_size, check_url_ascii, check_content_ascii, tokenize_url
from simhasing import sim_hash, compute_sim_hash_similarity
# from pickle_storing import pickle_data, load_pickled_data, crawl_data

"""
Response
--------
url: contains the url of the page request
status: contains the status code of the request
error: contains the error of the request
raw_reponse: contains the text of the page

Methods for checking traps
--------------------------
1. hash the content of the page (urls may be different but content same)
2. keep track of set of urls
3. check for repetitions within urls paths
"""
valid_domains = [r"^((.*\.)*ics\.uci\.edu)$", r"^((.*\.)*cs\.uci\.edu)$",
                r"^((.*\.)*informatics\.uci\.edu)$", r"^((.*\.)*stat\.uci\.edu)$"]
traps = r"^.*calendar.*$|^.*filter.*$"
valid_set = set()
visited_set = set()
url_hashes = set()
content_hashes = set() 
content = dict()
content_file = dict()

ics_subdomains = dict()
global_frequencies = dict()

# crawl_data = return_crawl_data()

def scraper(url, resp):
    from pickle_storing import crawl_data, pickle_data
    # Adds the url to a visited set of URL's to keep track of how far along we are
    crawl_data["visited_urls"].add(url)
    pickle_data(crawl_data, "current_crawl_data.pickle")
    # print(crawl_data["valid_urls"])
    # print(crawl_data["invalid_urls"])
    # print(crawl_data["url_hashes"])
    # print(crawl_data["content_hashes"])
    # print(crawl_data["content"])
    # print(crawl_data["content_file"])
    # print(crawl_data["ics_subdomains"])
    # print(crawl_data["global_frequencies"])

    if url in visited_set:
        return []

    visited_set.add(url)

    if not check_url_ascii(url) or not is_valid(url):
        return []
    
    url_freq = tokenize_url(url)
    url_hash = sim_hash(url_freq)

    try:
        if (resp.status == 200 and resp.raw_response and resp.raw_response.content):
            flag, disallows = check_robot_permission(url)
            if not flag: # cannot access page
                return []

            if len(resp.raw_response.content) > 1000000 or not check_content_ascii(resp.raw_response.content):
                return []
            
            if not check_url(url_hash):
                valid_set.add(url)
                ics_subdomain(url)
                content[url] = total_tokens # [content folder num, total tokens]
                return []

            url_hashes.add(url_hash)
            
            tokens = tokenize_content(resp.raw_response.content) # get tokens
            frequencies = token_frequencies(tokens) # compute token frequencies
            hash_vector = sim_hash(frequencies) # compute the hash for the content
            total_tokens = len(tokens)
            
            valid_set.add(url)
            ics_subdomain(url)
            content[url] = total_tokens # [content folder num, total tokens]

            if check_content(hash_vector, similarity_threshold=.95): # check if the content is unique or does not meet thresholds
                # file_number = len(valid_set)
                # filename = f"content/{file_number}.txt"
                # content_file[url] = file_number
                # write_to_file(filename, resp.raw_response.content)
                add_token_to_frequencies(tokens)
                content_hashes.add(hash_vector)
                links = extract_next_links(url, resp) # extract the links
            else:
                return []
            
            save_data()

            return [link for link in links if is_valid(link, disallows)]
        elif resp.status in set([301, 302, 308, 309]) and resp.raw_response and resp.url:
            flag, disallows = check_robot_permission(url)
            if not flag: # cannot access page
                return []
            
            location = resp.url
            redirected_url = create_absolute_url(url, location)
            if  redirected_url not in visited_setand and \
                is_valid(redirected_url):
                    valid_set.add(url)
                    ics_subdomain(url)
                    return [redirected_url]
            else:
                return []
        else:
            return []
    except:
        return []

# This function needs to return a list of urls that are scraped from the response. 
# (An empty list for responses that are empty). These urls will be added to the Frontier 
# and retrieved from the cache. These urls have to be filtered so that urls that do not 
# have to be downloaded are not added to the frontier.

def extract_next_links(url, resp) -> list:
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    
    #if resp.status == 200 and resp.raw_response.content:
    text = resp.raw_response.content
    new_urls  = set()
    soup = BeautifulSoup(text, "html.parser") # gets the text
    for tag in soup.find_all('a', href=True):
        if tag.get('href'):
            new_url = tag['href']
            absolute_url = create_absolute_url(url, new_url)
            if  absolute_url not in visited_set and \
                check_url_ascii(absolute_url) and \
                is_valid(absolute_url):
                    new_urls.add(absolute_url)
            else:
                visited_set.add(absolute_url)
    return list(new_urls)
    
def create_absolute_url(base_url, new_url):
    new_url = new_url.split('#', 1)[0].strip()
    absolute_url = urljoin(base_url, new_url, allow_fragments=False)
    return absolute_url
    

def check_robot_permission(url) -> bool:
    parsed = urlparse(url)
    scheme = parsed.scheme
    domain = parsed.netloc
    robots_file_url = f"{scheme}://{domain}/robots.txt"
    
    try: 
        response = requests.get(robots_file_url)
    except:
        return False, None

    if response.status_code == 200:
        robot_html_text = response.text
        return True, parse_robots_txt_for_disallows(robot_html_text), 
    else:
        return False, None

def parse_robots_txt_for_disallows(robots_txt, user_agent='*') -> set:
    """ Parse the robots.txt to find all disallowed paths for the given user-agent. """
    disallow_paths = []
    finished = False
    found_agents = False

    # Split the file into lines
    for line in robots_txt.splitlines():
        # print(line)
        line = line.split('#', 1)[0].strip()  # Defragment the url using (split '#') and take the 1st
        if not line:
            continue  # Skip empty lines

        if ':' in line:
            key, value = line.split(':', 1) # split line into two tokens
            key = key.strip().lower()
            value = value.strip()

            if key == 'user-agent':
                if value == user_agent and not finished:
                    found_agents = True
                else:
                    if found_agents and finished:
                        return set(disallow_paths)
            elif key == 'disallow' and found_agents:
                finished = True
                if value:  # Ignore empty Disallow directives which mean allow everything
                    disallow_paths.append(value)
                
    return set(disallow_paths)

# Find specified crawl delay value for the page being searched
def parse_robots_txt_for_crawl_delay(robots_txt, user_agent = '*') -> int:
    finished = False
    found_delay = False
    crawl_delay = None

    for line in robots_txt.read().splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue

        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip() 
            if key == "user-agent":
                if value == user_agent and not finished:
                    found_delay = True
                elif found_delay:
                    break
            elif key == "crawl-delay" and value:
                    crawl_delay = int(value)
                    finished = True
    return crawl_delay if crawl_delay and found_delay and finished else 2 # A delay of 2 (seconds) seems to be the standard delay for crawling websites
''
def find_all_sitemaps(robots_txt, keyword = "sitemap") -> list:
    sitemaps = []
    for line in robots_txt.read().splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            if key == keyword:
                sitemaps.append(value)
    return sitemaps


def ics_subdomain(url):
    parsed = urlparse(url)
    if (re.match(valid_domains[0], parsed.netloc)):
        path = f"{parsed.scheme}://{parsed.netloc}"
        if path in ics_subdomains:
            ics_subdomains[path] += 1
        else:
            ics_subdomains[path] = 1


def is_valid(url, disallows = []) -> bool:
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
        
        if check_for_repeating_dirs(url) or check_for_traps(url):
            return False

        for disallowed_link in disallows:
            pattern = re.compile(disallowed_link, re.I)
            if re.match(pattern, parsed.path):
                return False
        
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|mpg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|war|img|apk|py|cp|h|ff"
            + r"|thmx|mso|arff|rtf|jar|csv|bib|java|m|cc|odp|class|mexglx"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|pov|sh|c)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
 
# Tokenize contents of a .txt file using a buffer and reading by each char!

def check_url(new_hash_vector, similarity_threshold = 0.8):
    """Check if the new content set is exact or approximately similar to existing sets."""

    # Check for exact match first
    if new_hash_vector in url_hashes:
        return False  # Exact match found, content is not unique

    # Check for approximate similarity
    for hash_vector in url_hashes:
        if compute_sim_hash_similarity(new_hash_vector, hash_vector) > similarity_threshold:
            return False  # Similar content found, content is not unique

    return True  # Content is unique

def check_content(new_hash_vector, similarity_threshold = 0.8):
    """Check if the new content set is exact or approximately similar to existing sets."""

    # Check for exact match first
    if new_hash_vector in content_hashes:
        return False  # Exact match found, content is not unique

    # Check for approximate similarity
    for hash_vector in content_hashes:
        if compute_sim_hash_similarity(new_hash_vector, hash_vector) > similarity_threshold:
            return False  # Similar content found, content is not unique

    return True  # Content is unique

def save_data():
    num_pages = len(valid_set)
    longest_page = max(content, key=content.get)
    top_50 = sorted(global_frequencies.items(), key=lambda x: (x[0])) # sort in alphabetical order
    top_50 = sorted(top_50, key=lambda x: (x[1]), reverse=True) [:50]
    statistics = {"Unique Pages":num_pages, "Longest Page":longest_page, "Top 50":top_50, "ICS domain":ics_subdomains}
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
        for k, v in ics_subdomains.items():
            file.write(f"{k}: {v}\n")

def add_token_to_frequencies(tokens):
    for token in tokens:
        if token in global_frequencies:
            global_frequencies[token] += 1
        else:
            global_frequencies[token] = 1
    # save the frequencies here

# Custom alpha numeric function that includes ' using regex
def is_alpha_num(char) -> bool:
    pattern = r"[a-z0-9']"
    return re.match(pattern, char.lower()) or False
    
# JUST TEMP COUNT FUNCTION TO TEST SAME TOKENS ARE BEING COUNTED FROM PAGE TO PAGE
def count_common_tokens(set1, set2) -> int: # TO BE DELETED WHEN DONE COUNTING
    common_tokens = set1.intersection(set2)
    return len(common_tokens)

def check_for_repeating_dirs(url) -> bool:
    pattern = r"^.*?(/.+?/).*?\1.*$|^.*?/(.+?/)\2.*$"
    if re.match(pattern, url):
        return True
    return False

def check_for_traps(url) -> bool:
    if re.match(traps, url):
        return True
    return False

if __name__ == "__main__":
    # testing is_valid function
    """
    print(is_valid("https://archive.ics.uci.edu/path/path/path/path"))
    print(is_valid("https://ics.uci.edu/"))
    print(is_valid("https://youtube.com/"))
    with open("/Users/shika/Downloads/robots.txt", 'r') as f:
        print(parse_robots_txt_for_disallows(f))
    print()
    with open("/Users/shika/Downloads/Arobots.txt", 'r') as f:
        print(parse_robots_txt_for_disallows(f))
    print()
    with open("/Users/shika/Downloads/YTrobots.txt", 'r') as f:
        print(parse_robots_txt_for_disallows(f))
    """

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
    # my_list = tokenize100(text_content)
    # print(my_list)
    # print(len(my_list))
    # my_list1 = tokenize1("webpage_text.txt")
    # print(len(my_list1))

    # # Testing similar tokens in the two "my_lists"
    # count = count_common_tokens(set(my_list),set(my_list1))
    # print(count)


    # Testing crawl delay function
    # with open("/Users/shika/Downloads/stacks2robots.txt", 'r') as f:
    #     print("Crawl Delay is:", parse_robots_txt_for_crawl_delay(f))

    # Testing gathering sitemaps
    with open("/Users/shika/Downloads/robots.txt", 'r') as txt_file:
        print("List of sitemaps:",len(find_all_sitemaps(txt_file)))

        # check for traps 
            # algorithm for similarity
    #comment