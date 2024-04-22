import requests, re
from bs4 import BeautifulSoup
from simhasing import sim_hash, compute_sim_hash_similarity
from scraper import check_for_repeating_dirs, create_absolute_url
from urllib.parse import urlparse, urljoin
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
    "you're", "you've", "your", "yours", "yourself", "yourselves", "b", "c", "d", "e", 
    "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", 
    "w", "x", "y", "z"
])

def check_url(url) -> bool:
    parsed = urlparse(url)
    domain = parsed.netloc
    pattern = r"^((.*\.)*ics\.uci\.edu)$"
    if re.match(pattern, domain):
        return True
    return False

def tokenize_content(resp) -> list:
    soup = BeautifulSoup(resp.text, "html.parser")
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

def token_frequencies(tokens):
    token_freq = dict()
    for token in tokens:
        if token in token_freq:
            token_freq[token] += 1
        else:
            token_freq[token] = 1
    return token_freq

def is_alpha_num(char) -> bool:
    pattern = r"[a-z0-9']"
    return re.match(pattern, char.lower()) or False

if __name__ == "__main__":
    # resp1 = requests.get("https://ics.uci.edu/2017/11/08/new-faculty-spotlight-professor-vijay-vazirani-continues-groundbreaking-research/")
    # resp2 = requests.get("https://ics.uci.edu/2017/11/13/los-angeles-times-uci-computer-game-explores-culture-of-18th-century-ghana-el-zarki-quoted/")
    
    resp1 = requests.get("https://www.cs.uci.edu/new-faculty-spotlight-professor-vijay-vazirani-continues-groundbreaking-research")
    resp2 = requests.get("https://www.cs.uci.edu/los-angeles-times-uci-computer-game-explores-culture-of-18th-century-ghana-el-z         arki-quoted")
    
    tokens1 = tokenize_content(resp1)
    tokens2 = tokenize_content(resp2)

    frequencies1 = token_frequencies(tokens1)
    frequencies2 = token_frequencies(tokens2)

    hash1 = sim_hash(frequencies1)
    hash2 = sim_hash(frequencies2)

 
    print(compute_sim_hash_similarity(hash1, hash2))
    # http://http:www.ics.uci.edu/~jacobson/ics21/LabManual/00-LabManual.html
    print(check_for_repeating_dirs("https://www.cs.uci.edu/path/lies/beef"))
    print(check_url("https://wics.ics.uci.edu/employment/employ_distinguished.php"))

    