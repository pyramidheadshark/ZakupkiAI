import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
import time

def parse_page(url, headers):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    question_element = soup.find(class_='questionText')
    if question_element:
        question = question_element.find('p').text.strip()
        answer = question_element.find_all_next(name='p')
        text = '\n'.join(paragraph.text.strip() for paragraph in answer)

        data = {
            'question': question,
            'text': text,
            'link': url
        }
        return data

    return None


def crawl_website(start_url, headers):
    page_number = 1
    while True:
        url = f"{start_url}?&page={page_number}&pageSize=10"
        try:
            response = requests.get(url, headers=headers, timeout=10)  # Add a timeout of 10 seconds
        except requests.Timeout:
            print(f"Request to {url} timed out")
            break

        soup = BeautifulSoup(response.content, 'html.parser')

        links = soup.find_all('a', class_='colorBlack')
        for link in links:
            link_url = link.get('href')
            absolute_url = urljoin(start_url, link_url)
            page_data = parse_page(absolute_url, headers)
            if page_data:
                with open('data.json', 'a', encoding='utf-8') as f:
                    json.dump(page_data, f, indent=4, ensure_ascii=False)
                    f.write('\n')
                    time.sleep(0.01)

        next_button = soup.find('a', class_='paginator-button-next')
        if next_button:
            page_number += 1
        else:
            break

if __name__ == '__main__':
    start_url = 'https://zakupki.gov.ru/epz/main/public/qa/view.html?&&page=1&pageSize=50'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
    }
    crawl_website(start_url, headers)