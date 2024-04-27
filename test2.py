import test
from pickle_storing import load_pickled_data

if __name__ == "__main__":
    
    crawl_data = load_pickled_data("current_crawl_data.pickle")
    if crawl_data:
        print("Loading Pickled Data")
    else:
        print("Nothing in pickle file")
