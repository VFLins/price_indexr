from bs4 import BeautifulSoup
import requests
import time

def connect():
    SEARCH_FIELD = "msi geforce rtx 4060 ti 16gb gaming x"

    SEARCH_HEADERS = {
        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.76"}

    BING_SEARCH_PARAMS = {"q" : SEARCH_FIELD}
    BING_SEARCH_RESPONSE = requests.get(
        "https://www.bing.com/shop",
        params = BING_SEARCH_PARAMS,
        headers = SEARCH_HEADERS)

    GOOGLE_SEARCH_PARAMS = {"q" : SEARCH_FIELD, "tbm" : "shop"}
    GOOGLE_SEARCH_RESPONSE = requests.get(
        "https://www.google.com/search",
        params = GOOGLE_SEARCH_PARAMS,
        headers = SEARCH_HEADERS)

    ### Ensure data was collected
    try:
        try_con = 1
        maximum_try_con = 10
        while try_con <= maximum_try_con:
            
            soup_google = BeautifulSoup(GOOGLE_SEARCH_RESPONSE.text, "lxml")
            google_grid = soup_google.find_all("div", {"class": "sh-dgr__content"})
            google_inline = soup_google.find_all("div", {"class": "KZmu8e"})
            google_highlight = soup_google.find("div", {"class": "_-oX"}) # might bring up to 3 results but will count as 1

            soup_bing = BeautifulSoup(BING_SEARCH_RESPONSE.text, "lxml")
            bing_grid = soup_bing.find_all("li", {"class": "br-item"})
            bing_inline = soup_bing.find_all("div", {"class": "slide", "data-appns": "commerce", "tabindex": True})

            google_n_results = len(google_grid) + len(google_inline)
            if google_highlight:
                google_n_results = google_n_results + len(google_highlight)
            bing_n_results = len(bing_grid) + len(bing_inline)

            if ((google_n_results > 0) and (bing_n_results > 0)):
                break
            
            try_con = try_con + 1
            if try_con > maximum_try_con: raise ConnectionError("Maximum number of connection attempts exceeded")
    except TimeoutError as connection_error:
        print(connection_error, "Couldn't obtain data, check your internet connection or User-Agent used on the source code.")
        quit()
    except Exception as unexpected_error:
        print(unexpected_error, "Unexpected error, closing connection...")
        quit()
    
    messages = ["google_grid", "google_inline", "google_highlight", "bing_grid", "bing_inline"]
    objs = [google_grid, google_inline, google_highlight, bing_grid, google_inline]

    print(f"number of connection attempts: {try_con}")
    for m, o in zip(messages, objs):
        if o:
            print(f"{m}: {len(o)}")
        else:
            print(f"{m}: empty")

if __name__ == "__main__":
    start_time = time.time()
    connect()
    end_time = time.time()

    print(f"\nconnect time: {end_time-start_time}")