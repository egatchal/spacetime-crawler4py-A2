import re, requests, cbor
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from utils import  normalize


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
valid_domains = [r".*\.ics\.uci\.edu", r".*\.cs\.uci\.edu",
                r".*\.informatics\.uci\.edu", r".*\.stat\.uci\.edu"]
stopwords_list = set([
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", 
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being", 
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", 
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", 
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", 
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", 
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", 
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", 
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", 
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", 
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", 
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", 
    "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there", 
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", 
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", 
    "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", 
    "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", 
    "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", 
    "you're", "you've", "your", "yours", "yourself", "yourselves"
])

valid_set = set()
invalid_set = set()

content = dict()
ics_subdomains = set()
frequencies = dict()

content_sets = []

def scraper(url, resp):
    # robot.txt check goes here
    if url in valid_set or url in invalid_set:
        return []
    
    if not is_valid(url):
        invalid_set.add(url)
        return []
    
    flag, disallows = check_robot_permission(url)
    if not flag: # cannot access page
        invalid_set.add(url)
        return []
    
    if (resp.status == 200 and resp.raw_response.content):
        valid_set.add(url)
        if is_ics_subdomain(url):
            ics_subdomains.add(url)

        tokens = tokenize_content(resp)
        content[url] = len(tokens)
        compute_token_frequencies(tokens) # compute token frequencies and add to frequencies
        save_data() 
        links = extract_next_links(url, resp)
        return [link for link in links if is_valid(link, disallows)]
    elif resp.status in set([301, 302]) and resp.raw_response.url:
        location = resp.raw_response.url
        if location:
            redirected_url = urljoin(url, location)
            if redirected_url not in valid_set and redirected_url not in invalid_set:
                return [redirected_url]
        else:
            invalid_set.add(url)
            return []
    else:
        invalid_set.add(url)
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
        new_url = tag['href']
        absolute_url = urljoin(url, new_url)
        absolute_url = absolute_url.split('#', 1)[0].strip() # defragment the url
        absolute_url = normalize(absolute_url)
        if absolute_url not in valid_set and absolute_url not in invalid_set:
            new_urls.add(absolute_url)

    return list(new_urls)
    

''' MODIFIED VERSION OF extract_next_links:
def extract_next_links(base_url, resp, disallows):
    links = set()

    # Handle 200 OK: Directly parse content
    if resp.status == 200 and resp.raw_response.content:
        soup = BeautifulSoup(resp.raw_response.content, "html.parser")  # Parse the HTML content
        for link_tag in soup.find_all('a', href=True):
            abs_url = urljoin(base_url, link_tag['href'])  # Normalize the URL
            if is_valid(abs_url):  # Check validity using the existing function
                links.add(abs_url)

    # Handle redirections (301, 302)
    elif resp.status in (301, 302):
        location = resp.headers.get('Location')
        if location:
            redirected_url = urljoin(base_url, location)
            if is_valid(redirected_url):  # Validate redirected URL
                links.add(redirected_url)

    # Additional status codes could be handled here if needed
    # For example, retrying or logging failures, etc.

    return list(links)
'''

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
        return True, parse_robots_txt_for_disallows(robot_html_text)
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


def is_ics_subdomain(url):
    parsed = urlparse(url)
    if (re.match(valid_domains[0], parsed.netloc)):
        return True
    return False


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
        
        if check_calendar(url):
            return False
        
        for disallowed_link in disallows:
            pattern = re.compile(disallowed_link, re.I)
            if re.match(pattern, parsed.path):
                return False
        
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
 
# # Tokenize contents of a url instead of a .txt file?
# def tokenize(url) -> list:
#     text_file = requests.get(url).text

# Tokenize contents of a .txt file using a buffer and reading by each char!
def tokenize_content(resp) -> list:
    soup = BeautifulSoup(resp.raw_response.content, "html.parser")
    text_tags = soup.find_all(['p','h1','h2','h3','h4','h5','h6','li','ul'])
    text_content = [tag.get_text(separator = " ", strip = True) for tag in text_tags]

    token_list = []
    token = ''
    for line in text_content:
        for char in line:
            char = char.lower()
            if is_alpha_num(char):
                token += char
            else:
                if token:
                    if token not in stopwords_list:
                        token_list.append(token)
                    token = ''
        if token:
            if token not in stopwords_list:
                token_list.append(token)
            token = ''

    return token_list

def jaccard_similarity(set1, set2):
    """Calculate the Jaccard Similarity between two sets."""
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union) if union else 0

def check_content(new_content_set):
    """Check if the new content set is exact or approximately similar to existing sets."""
    similarity_threshold = 0.5  # Define a threshold for similarity

    # Check for exact match first
    if new_content_set in content_sets:
        return False  # Exact match found, content is not unique

    # Check for approximate similarity
    for content_set in content_sets:
        if jaccard_similarity(new_content_set, content_set) > similarity_threshold:
            return False  # Similar content found, content is not unique

    # No match or similarity found, add to the list of content sets
    content_sets.append(new_content_set)
    return True  # Content is unique

def save_data():
    num_pages = len(valid_set)
    longest_page = max(content, key=content.get)
    top_50 = sorted(frequencies.items(), key=lambda x: (x[0])) # sort in alphabetical order
    top_50 = sorted(top_50, key=lambda x: (x[1]), reverse=True) [:50]
    statistics = {"Unique Pages":num_pages, "Longest Page":longest_page, "Top 50":top_50, "ICS domain":ics_subdomains}
    with open('statistics.txt', 'w') as file:
        # Write the statistics data to the file
        for key, value in statistics.items():
            file.write(f"{key}: {value}\n")

def compute_token_frequencies(tokens):
    for token in tokens:
        if token in frequencies:
            frequencies[token] += 1
        else:
            frequencies[token] = 1
    # save the frequencies here

# Custom alpha numeric function that includes ' using regex
def is_alpha_num(char) -> bool:
    pattern = r"[a-z0-9']"
    return re.match(pattern, char.lower()) or False

def check_calendar(url) -> bool:
    parse = urlparse(url)
    parts = parse.path.split("/")
    for i in range(len(parts)-1):
        if parts[i] == parts[i+1]:
            return True
    return False
    
# JUST TEMP COUNT FUNCTION TO TEST SAME TOKENS ARE BEING COUNTED FROM PAGE TO PAGE
def count_common_tokens(set1, set2) -> int: # TO BE DELETED WHEN DONE COUNTING
    common_tokens = set1.intersection(set2)
    return len(common_tokens)

def check_for_repeating_dirs(url, visited_directories) -> bool:
    pattern = r"^.*?(/.+?/).*?\1.*$|^.*?/(.+?/)\2.*$"
    for dir in visited_directories:
        if re.match(pattern, dir):
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