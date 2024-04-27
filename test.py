
valid_set = set()
visited_set = set()
content_hashes = set() 
content = dict()
content_file = dict()
ics_subdomains = dict()
global_frequencies = dict()
url_hashes = set()
url_path_count = dict()

def saving_data():
    from pickle_storing import pickle_data
    pickle_data(get_crawl_data(), "current_crawl_data.pickle")

def get_crawl_data():
    crawl_data = {
        "valid_urls": valid_set,
        "visited_urls": visited_set,
        "content_hashes": content_hashes,
        "content": content,
        "content_file": content_file,
        "ics_subdomains": ics_subdomains,
        "global_frequencies": global_frequencies,
        "url_hashes": url_hashes,
        "url_path_count": url_path_count
    }
    return crawl_data

def print_out_data():
    print(valid_set)
    print(visited_set)
    print(content_hashes)
    print(content)
    print(content_file)
    print(ics_subdomains)
    print(global_frequencies)
    print(url_hashes)

