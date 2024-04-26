import requests, re
from bs4 import BeautifulSoup
from simhasing import sim_hash, compute_sim_hash_similarity
import os

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
    "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"
])

# delimiter_patterns = r'[:;,.=\+\-%_?&%\s\/\\]+'
delimiter_patterns = r'[\/]+'


def write_to_file(filename, text):
    current_directory = os.getcwd()
    current_directory = f"{current_directory}/{filename}"
    with open(current_directory,"wb") as file:
        file.write(text)

def check_file_size(filename):
    current_directory = os.getcwd()
    current_directory = f"{current_directory}/{filename}"
    return os.path.getsize(current_directory) / 1000000

def check_url_ascii(text):
    for c in text:
        ascii_value = ord(c)
        if ascii_value < 0 or ascii_value > 255:
            return False
    return True

def check_content_ascii(content):
    for byte in content:
        if byte < 0 or byte > 255:
            return False
    return True

def tokenize_content(text) -> list:
    text_tags = BeautifulSoup(text, "html.parser")
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

def tokenize_url(url):
    token_list = []
    token = ''
    for char in url:
        char = char.lower()
        if is_alpha_num(char):
            token += char
        else:
            if token:
                token_list.append(token)
                token = ''
    if token:
        token_list.append(token)
        token = ''

    token_freq = token_frequencies(token_list)
    return token_freq


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
    # resp1 = requests.get("https://ics.uci.edu/facts-figures/ics-mission-history/")
    # resp2 = requests.get("http://www.ics.uci.edu/about/search")
    resp1 = "https://ics.uci.edu/~dechter/publications/r64.html"
    resp2 = "https://ics.uci.edu/~dechter/publications/r255.html"
    # print(check_url_ascii(url))
    # print(check_content_ascii(resp.content))
    tokens1 = tokenize_url(resp1)
    tokens2 = tokenize_url(resp2)
    
    # tokens1 = tokenize_content(resp1.content)
    # tokens2 = tokenize_content(resp2.content)
    
    print(tokens1)
    print(tokens2)
    
#     frequencies1 = token_frequencies(tokens1)
#     frequencies2 = token_frequencies(tokens2)

#     hash1 = sim_hash(frequencies1)
#     hash2 = sim_hash(frequencies2)
    hash1 = sim_hash(tokens1)
    hash2 = sim_hash(tokens2)
    print(compute_sim_hash_similarity(hash1, hash2))
    # filename = "read_page.txt.txt"
    # resp = requests.get("http://www.ics.uci.edu/~eppstein/junkyard/all.html")
    # write_to_file(filename, resp.text)
    # print(check_file_size(filename))
    # value = tuple([1,1,0,1,1,])
    # print(value)
    # print(str(value))
    pass


