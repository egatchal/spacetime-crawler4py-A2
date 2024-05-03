# from scraper import valid_set, visited_set, content_hashes, content, content_file, ics_subdomains, global_frequencies, url_hashes, url_path_count
import pickle
import scraper

def pickle_data(crawl_data, filename):
    """Serialize data to a file using the Pickle library.

    Parameters
    ----------
    crawl_data : dict
        a dict of containers that store data on previously crawled websites
    filename : str
        the file name of where the pickled data will be stored
    """
    with open(filename, "wb") as file:
        pickle.dump(crawl_data, file)

def load_pickled_data(filename):
    """Deserialize data from a pickled file.

    Parameters
    ----------
    crawl_data : dict

    Returns
    -------
    bool
        a bool indicating whether the data was successfully deserialized
    """
    try:
        with open(filename, "rb") as content:
            d = pickle.load(content)
            scraper.valid_set = d.get("valid_urls")
            scraper.visited_set = d.get("visited_urls")
            scraper.content_hashes = d.get("content_hashes")
            scraper.content = d.get("content")
            scraper.content_file = d.get("content_file")
            scraper.ics_subdomains = d.get("ics_subdomains")
            scraper.global_frequencies = d.get("global_frequencies")
            scraper.url_hashes = d.get("url_hashes")
            scraper.url_path_count = d.get("url_path_count")
        return True
    except FileNotFoundError: 
        return None

