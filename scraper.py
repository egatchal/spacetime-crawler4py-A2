import re, requests, cbor
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from utils import  normalize
from utils.response import Response

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
valid_domains = [r".*\.*ics\.uci\.edu", r".*\.*cs\.uci\.edu",
                r".*\.*informatics\.uci\.edu", r".*\.*stat\.uci\.edu"]
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
    
    
    flag, disallows = check_robot_permission(url)
    if not flag: # cannot access page
        return []
    
    # function - "tokenize" extract all tokens here (exclude urls)

    links = extract_next_links(url, resp, disallows)
    
    return [link for link in links if is_valid(link)]

# This function needs to return a list of urls that are scraped from the response. 
# (An empty list for responses that are empty). These urls will be added to the Frontier 
# and retrieved from the cache. These urls have to be filtered so that urls that do not 
# have to be downloaded are not added to the frontier.

def extract_next_links(url, resp, disallows) -> list:
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
    if resp.status == 200 and text:
        soup = BeautifulSoup(text, "html.parser") # gets the text
        links  = set()
        for link in soup.find_all('a', href=True):
            link = link['href']
            for disallowed_link in disallows:
                pattern = re.compile(disallowed_link, re.I)
                if re.match(pattern, parsed.path):
                    # print(f"Checked: {parsed.path}, Disallow: {pattern}")
                    check = False
                    break
            
            if check:
                links.add(link)
        return links
    return list()

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

# def find_all_sitemaps(robots_txt, keyword = "sitemap") -> list:
#     sitemaps = []
#     for line in robots_txt.read().splitlines():
#         line = line.split('#', 1)[0].strip()
#         if not line:
#             continue
#         if ':' in line:
#             key, value = line.split(':' 1)
#             key = key.strip().lower()
#             if key == keyword:

        

def is_valid(url) -> bool:
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
 
# # Tokenize contents of a url instead of a .txt file?
# def tokenize(url) -> list:
#     text_file = requests.get(url).text

# Tokenize contents of a .txt file using a buffer and reading by each char
def tokenize(text_file) -> list:
    token_list = []
    with open(text_file, 'r') as file:
        while True:
            buffer = file.read(1024)
            if not buffer:
                break
            token = ''
            for char in buffer:
                if is_alpha_num(char):
                    token += char.lower()
                else:
                    if token:
                        token_list.append(token)
                        token = ''
            if token and not file.read(1): 
                token_list.append(token)
    return token_list

# Strictly testing !
def tokenize100(text_file) -> list:
    token_list = []
    token = ''
    for line in text_file:
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

# Tokenize contents of a .txt file using a buffer and reading by line
def tokenize1(text_file) -> list:
    token_list = []
    with open(text_file, 'r') as file:
        for line in file:
            token = ''
            for char in line:
                if is_alpha_num(char):
                    token += char.lower()
                else:
                    if token:
                        token_list.append(token)
                        token = ''
            if token: 
                token_list.append(token)
    return token_list

# Tokenize contents of a .txt using a buffer of chars
def tokenize3(text_file) -> list:
    buffer_size = 1024 # can be changed to whatever you want
    last_line = False # last line flag
    token_list = []
    
    with open(text_file, 'r') as file:
        token = ''
        while (not last_line):
            buffer = file.read(buffer_size).lower()
            if (len(buffer) < buffer_size): # check if we're on the last line by checking the buffer size
                last_line = True
            
            for char in buffer:
                if is_alpha_num(char):
                    token += char.lower()
                else:
                    if token:
                        token_list.append(token)
                        token = ''
            
            if last_line and token: 
                token_list.append(token)

    return token_list
# Custom alpha numeric function that includes ' using regex
def is_alpha_num(char) -> bool:
    pattern = r"[a-z0-9']"
    return re.match(pattern, char.lower()) or False

# JUST TEMP COUNT FUNCTION TO TEST SAME TOKENS ARE BEING COUNTED FROM PAGE TO PAGE
def count_common_tokens(set1, set2) -> int: # TO BE DELETED WHEN DONE COUNTING
    common_tokens = set1.intersection(set2)
    return len(common_tokens)

if __name__ == "__main__":
    # testing is_valid function
    """
    print(is_valid("https://archive.ics.uci.edu/"))
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

    url = "https://spaces.lib.uci.edu/reserve/Science"
    # flag, disallows = check_robot_permission(url)
    
    # print(extract_next_links(url, url, disallows))

    # print(disallows)

    # # Testing retrieving tokens from a webpage
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    # soup = BeautifulSoup(response.raw_response.content, "html.parser")
    # text_tags = soup.find_all(['p','h1','h2','h3','h4','h5','h6','li','ul'])
    text_tags = soup.find_all(['p','h1','h2','h3','h4','h5','h6','li','ul'])
    # [print(tag.get_text()) for tag in text_tags]
    text_content = [tag.get_text(separator = " ", strip = True) for tag in text_tags]
    print(text_content)
    # text = ' '.join(text_content)

    # print(text_content)
    # # Downloading the file since the text is now too large to pass in
    # with open('webpage_text.txt', 'w', encoding='utf-8') as file:
    #     file.write(text_content)
    # Testing the tokenize function with the downloaded page as a text file
    # print(tokenize("webpage_text.txt"))

    # === Testing the lengths of lists being returned from a line-by-line read
    my_list = tokenize100(text_content)
    print(my_list)
    # print(len(my_list))
    # my_list1 = tokenize1("webpage_text.txt")
    # print(len(my_list1))

    # # Testing similar tokens in the two "my_lists"
    # count = count_common_tokens(set(my_list),set(my_list1))
    # print(count)


    # Testing crawl delay function
    # with open("/Users/shika/Downloads/nasarobots.txt", 'r') as f:
    #     print("Crawl Delay is:", parse_robots_txt_for_crawl_delay(f))


        # check for traps 
            # algorithm for similarity