import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin

def scrape_links(url, headers):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    links = []
    for a_tag in soup.find_all('a', class_='docs-title heading-h4'):
        link = a_tag.get('href')
        if link:
            absolute_url = urljoin(url, link)
            links.append({
                'name': a_tag.text.strip(),
                'url': absolute_url
            })

    return links


def crawl_website(start_url, headers):
    all_links = scrape_links(start_url, headers)

    with open('kodeks.json', 'w', encoding='utf-8') as f:
        json.dump(all_links, f, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    start_url = 'https://zakupki.gov.ru/epz/main/public/qa/view.html?&page=1&pageSize=200'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        'Accept': 'text/htmlы,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
    }
    crawl_website(start_url, headers)