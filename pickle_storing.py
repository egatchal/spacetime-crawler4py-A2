from scraper import valid_set, visited_set, content_hashes, content, content_file, ics_subdomains, global_frequencies, url_hashes
import pickle

crawl_data = {
    "valid_urls": valid_set,
    "visited_urls": visited_set,
    "content_hashes": content_hashes,
    "content": content,
    "content_file": content_file,
    "ics_subdomains": ics_subdomains,
    "global_frequencies": global_frequencies,
    "url_hashes": url_hashes
    # "url_depths": url_depth
}

def pickle_data(data_state, filename):
    with open(filename, "wb") as file:
        pickle.dump(data_state, file)

def load_pickled_data(filename):
    try:
        with open(filename, "rb") as content:
            return pickle.load(content)
    except FileNotFoundError: 
        return None
