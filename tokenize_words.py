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

def write_to_file(filename, text):
    """Write data from one file (filename) to another specified file (text).

    Parameters
    ----------
    filename : str
        file path to read data from
    text : str
        text is a file to write data to
    """
    current_directory = os.getcwd()
    current_directory = f"{current_directory}/{filename}"
    with open(current_directory,"wb") as file:
        file.write(text)

def check_url_ascii(text):
    """Check if content contains only valid ascii chars.

    Parameters
    ----------
    content : bytes
        content to be checked

    Returns
    -------
    bool
        a bool indicating if the content is only ascii
    """
    return text.isascii()

def tokenize_content(text) -> list:
    """Tokenizes the text file.

    Parameters
    ----------
    text : str
        text content as bytes

    Returns
    -------
    list
        a list of tokens from the text file
    """
    # Parse byte content to HTML content which is easier to navigate
    text_tags = BeautifulSoup(text, "html.parser")
    text_content = text_tags.get_text(" ")
    
    # Gathering all valid tokens from page content (char by char)
    token_list = []
    token = ''
    for char in text_content:
        char = char.lower()
        if is_alpha_num(char):
            token += char
        else:
            if token:
                if token not in stopwords_list and len(token) > 1:
                    token_list.append(token)
                token = ''
    if token:
        if token not in stopwords_list and len(token) > 1:
            token_list.append(token)
        token = ''

    return token_list

def tokenize_url(url):
    """Tokenizes the passed in URL.
    
    Parameters
    ----------
    url : str
        a URL to a website
    
    Returns
    -------
    dict
        a dict of the tokens (key) and their corresponding frequency count (value)
    """
    token_list = []
    token = ""
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

    return token_list


def token_frequencies(tokens):
    """Check the frequencies of each token.

    Parameters
    ----------
    tokens : list
        a list of tokens

    Returns
    -------
    dict
        a dict of tokens (key) with their corresponding frequency counts (value)
    """
    token_freq = dict()
    for token in tokens:
        if token in token_freq: # if the token has been seen before, we increment the count
            token_freq[token] += 1
        else:
            token_freq[token] = 1
    return token_freq

def is_alpha_num(char) -> bool:
    """Check if char is alphanumeric.

    Parameters
    ----------
    char : char
        char to be checked against the regex statement
    
    Returns
    -------
    bool
        a bool indicating whether the char is alphanumeric 
    """
    pattern = r"[a-z0-9]"
    return re.match(pattern, char.lower())

if __name__ == "__main__":
    # resp1 = requests.get("https://ics.uci.edu/facts-figures/ics-mission-history/")
    # resp2 = requests.get("http://www.ics.uci.edu/about/search")
    resp1 = "https://ngs.ics.uci.edu/from-calendars-to-chronicles-1"
    resp2 = "https://ngs.ics.uci.edu/from-calendars-to-chronicles-6"
    # print(check_url_ascii(resp2))
    # values = set()
    # values.add("hello")
    # values.add("bush")
    # values.add("hands")
    # values.add("guard")
    # print(list(values))
    # print(check_url_ascii(url))
    # print(check_content_ascii(resp.content))
    tokens1 = tokenize_url(resp1)
    tokens2 = tokenize_url(resp2)
    
    #     # tokens1 = tokenize_content(resp1.content)
    #     # tokens2 = tokenize_content(resp2.content)
        
    #     print(tokens1)
    #     print(tokens2)
    
    frequencies1 = token_frequencies(tokens1)
    frequencies2 = token_frequencies(tokens2)

    hash1 = sim_hash(frequencies1)
    hash2 = sim_hash(frequencies2)
    #     hash1 = sim_hash(tokens1)
    #     hash2 = sim_hash(tokens2)
    print(compute_sim_hash_similarity(hash1, hash2))
    # filename = "read_page.txt.txt"
    # resp = requests.get("http://www.ics.uci.edu/~eppstein/junkyard/all.html")
    # write_to_file(filename, resp.text)
    # print(check_file_size(filename))
    # value = tuple([1,1,0,1,1,])
    # print(value)
    # print(str(value))
    pass


