import requests
from storygraph_api.exception_handler import request_exception

class BooksScraper:
    @staticmethod
    @request_exception
    def fetch_url(url):
        response = requests.get(url)
        response.raise_for_status()
        return response.content

    @staticmethod
    @request_exception
    def fetch_url_authenticated(url, cookies):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, cookies=cookies, headers=headers)
        response.raise_for_status()
        return response.content

    @staticmethod
    def main(book_id):
        url = f"https://app.thestorygraph.com/books/{book_id}"
        return BooksScraper.fetch_url(url)

    @staticmethod
    def book_page_authenticated(book_id, cookies):
        url = f"https://app.thestorygraph.com/books/{book_id}"
        return BooksScraper.fetch_url_authenticated(url, cookies)

    @staticmethod
    def community_reviews(book_id):
        url = f"https://app.thestorygraph.com/books/{book_id}/community_reviews"
        return BooksScraper.fetch_url(url)

    @staticmethod
    def content_warnings(book_id):
        url = f"https://app.thestorygraph.com/books/{book_id}/content_warnings"
        return BooksScraper.fetch_url(url)

    @staticmethod
    def search(query):
        formatted_query = query.replace(' ', '%20')
        url = f"https://app.thestorygraph.com/browse?search_term={formatted_query}"
        return BooksScraper.fetch_url(url)