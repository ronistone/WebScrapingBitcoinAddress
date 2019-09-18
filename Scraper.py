from requests import get
from bs4 import BeautifulSoup
from BitcoinAddressValidator import get_all_bitcoin_address_from_text
from multiprocessing import Pool

import re
import signal

WORKERS = 20
REQUEST_TIMEOUT = 5
VERBOSE = True


class Scraper:
    visit = set()
    queue = []
    result = set()

    def __init__(self, callback):
        self.callback = callback

    @staticmethod
    def init_worker():
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def scraping(self, urls: list) -> None:
        self.init_scraping_search(urls)
        pool = Pool(WORKERS, self.init_worker)

        while len(self.queue):
            try:
                if VERBOSE:
                    print("visited: ", len(self.visit) - len(self.queue))
                    print("queue: ", len(self.queue))

                nextLinksToProcess = self.get_next()

                links = self.process_next(nextLinksToProcess, pool)

                self.find_links_to_continue_search(links)

                if VERBOSE:
                    print("=======")
            except Exception as e:
                print(e)
                pool.terminate()
                break

    def init_scraping_search(self, urls: list) -> None:
        self.queue.extend(urls)
        for url in urls:
            self.visit.add(url)

    def find_links_to_continue_search(self, links: list) -> None:
        for link in links:
            if link not in self.visit:
                self.visit.add(link)
                self.queue.append(link)

    def process_next(self, next: list, pool) -> list:
        linksAndResult = pool.map(self.process_url, next)

        links = [link for sublinks, results in linksAndResult for link in sublinks]

        resultList = [result for sublinks, results in linksAndResult for result in results]

        if VERBOSE:
            print(resultList)

        self.result = self.result.union(resultList)

        return links

    def get_next(self) -> list:
        next = []
        for i in range(WORKERS):
            if not len(self.queue):
                break
            next.append(self.queue.pop(0))
            if VERBOSE:
                print(next[i])
        return next

    def process_url(self, next: str) -> tuple:
        result = []
        try:
            request = get(next, timeout=REQUEST_TIMEOUT)

            if request.content is not None and len(request.content):
                content = request.content
                if self.callback is not None:
                    result = self.callback(content.decode())
                else:
                    raise Exception('Callback is required to process page!')

                links = self.find_all_links(content)

                if links is not None:
                    return links, result
        except Exception as e:
            print('Treat exception!', e)
        return [], result

    def find_all_links(self, content: str) -> set:
        soup = BeautifulSoup(content, 'html.parser')
        return set(a.get('href') for a in soup.findAll('a', attrs={'href': re.compile("https?://")}))


if __name__ == '__main__':
    scraper = Scraper(get_all_bitcoin_address_from_text)

    try:
        scraper.scraping(['https://www.blockchain.com/pt/btc/address/1F1tAaz5x1HUXrCNLbtMDqcw6o5GNn4xqX',
                          'https://www.blockchain.com/pt/btc/address/1UZhhzWo85osGzNrs1BVjoE3FP8ea2umX'])
        # 'https://github.com/explore',
        # 'https://br.investing.com/crypto/bitcoin/chat',
        # 'https://medium.com/blockchannel/blockchain-communities-and-their-emergent-governance-fdf24329551f'])
    except KeyboardInterrupt:
        pass
    print(scraper.result)
    print(len(scraper.result))
