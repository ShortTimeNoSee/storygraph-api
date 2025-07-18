from storygraph_api.request.books_request import BooksScraper
from storygraph_api.exception_handler import parsing_exception
from bs4 import BeautifulSoup, Tag, NavigableString
import re
from typing import Dict, Any, List

class BooksParser:
    @staticmethod
    @parsing_exception
    def book_page(book_id: str) -> Dict[str, Any]:
        content = BooksScraper.main(book_id)
        soup = BeautifulSoup(content, 'html.parser')

        h3_tag = soup.find('h3', class_="font-serif font-bold text-2xl md:w-11/12")
        if not isinstance(h3_tag, Tag):
            raise Exception("Could not find the main title header.")

        title = ""
        if h3_tag.contents and isinstance(h3_tag.contents[0], NavigableString):
            title = h3_tag.contents[0].strip()

        authors = []
        for a in h3_tag.find_all('a'):
            if isinstance(a, Tag):
                href = a.get("href")
                if isinstance(href, str) and href.startswith("/authors"):
                    authors.append(a.text)

        p_tag = soup.find('p', class_="text-sm font-light text-darkestGrey dark:text-grey mt-1")
        if not isinstance(p_tag, Tag) or not p_tag.contents:
            raise Exception("Could not find book metadata paragraph.")

        pages_text = p_tag.contents[0]
        pages = pages_text.strip().split()[0] if isinstance(pages_text, NavigableString) else "N/A"

        pub_info_spans = p_tag.find_all('span')
        first_pub = pub_info_spans[1].text.split()[-1] if len(pub_info_spans) > 1 else "N/A"

        tag_div = soup.find('div', class_="book-page-tag-section")
        tags = [tag.text for tag in tag_div.find_all('span')] if isinstance(tag_div, Tag) else []

        script_tags = soup.find_all('script')
        desc = ""
        for s in script_tags:
            if 'Description</h4>' in s.text:
                desc = s.text
                break

        pattern = re.compile(r"Description</h4><div class=\"trix-content mt-3\">(.*?)</div>", re.DOTALL)
        match = pattern.search(desc)
        description = match.group(1).strip() if match else "Description not found."

        review_content = BooksScraper.community_reviews(book_id)
        rev_soup = BeautifulSoup(review_content, 'html.parser')
        avg_rating_span = rev_soup.find('span', class_="average-star-rating")
        avg_rating = avg_rating_span.text.strip() if avg_rating_span else "N/A"

        warnings = BooksParser.content_warnings(book_id)

        data = {
            'title': title, 'authors': authors, 'pages': pages,
            'first_pub': first_pub, 'tags': tags, 'average_rating': avg_rating,
            'description': description, 'warnings': warnings
        }
        return data

    @staticmethod
    @parsing_exception
    def reading_progress(book_id: str, cookies: Dict[str, str]) -> str:
        content = BooksScraper.book_page_authenticated(book_id, cookies)
        soup = BeautifulSoup(content, 'html.parser')

        progress_bar_div = soup.find('div', class_='progress-bar')
        if not isinstance(progress_bar_div, Tag):
            raise Exception("Could not find progress bar. Ensure book is 'currently-reading'.")

        progress_span = progress_bar_div.find('span')
        if isinstance(progress_span, Tag) and progress_span.string:
            return progress_span.string.strip()

        inner_div = progress_bar_div.find('div', style=lambda v: 'width: 0%' in v if v else False)
        if inner_div is not None:
            return "0%"

        raise Exception("Could not extract percentage from progress bar.")

    @staticmethod
    @parsing_exception
    def content_warnings(book_id: str) -> Dict[str, List[str]]:
        warnings_content = BooksScraper.content_warnings(book_id)
        warnings_soup = BeautifulSoup(warnings_content, 'html.parser')

        standard_panes = warnings_soup.find_all('div', class_='standard-pane')
        if len(standard_panes) < 2:
            return {'graphic': [], 'moderate': [], 'minor': []}

        user_warnings_pane = standard_panes[1]
        warnings: Dict[str, List[str]] = {'graphic': [], 'moderate': [], 'minor': []}
        current_list_key = 'graphic'
        tag_re = re.compile(r'^(.*) \((\d+)\)$')

        for tag in user_warnings_pane.children:
            if not isinstance(tag, Tag): continue

            if tag.name == 'p':
                if tag.text == 'Graphic': current_list_key = 'graphic'
                elif tag.text == 'Moderate': current_list_key = 'moderate'
                elif tag.text == 'Minor': current_list_key = 'minor'
            elif tag.name == 'div':
                match = tag_re.match(tag.text)
                if match: warnings[current_list_key].append(match.group(1))
        return warnings

    @staticmethod
    @parsing_exception
    def search(query: str) -> List[Dict[str, str]]:
        content = BooksScraper.search(query)
        soup = BeautifulSoup(content, 'html.parser')
        search_results: List[Dict[str, str]] = []

        books = soup.find_all('div', class_="book-title-author-and-series w-11/12")
        for book in books:
            if not isinstance(book, Tag): continue

            title_tag = book.find('a')
            title = title_tag.text.strip() if isinstance(title_tag, Tag) else "N/A"

            href_val = title_tag.get('href') if isinstance(title_tag, Tag) else None

            href = href_val[0] if isinstance(href_val, list) else href_val
            book_id = href.split('/')[-1] if isinstance(href, str) else "N/A"

            author = "N/A"
            for a_tag in book.find_all('a'):
                if isinstance(a_tag, Tag):
                    href = a_tag.get("href")
                    if isinstance(href, str) and href.startswith('/author'):
                        author = a_tag.text.strip()
                        break

            search_results.append({'title': title, 'author': author, 'book_id': book_id})

        return search_results
