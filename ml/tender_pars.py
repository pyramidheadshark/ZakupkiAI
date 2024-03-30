import requests
import re
from bs4 import BeautifulSoup as bs
from time import sleep
import json

HTTP_TIMEOUT = 2
amount = 2
api = None
list_of_company = ['БОЛЬНИЦА', 'ФИЗИЧЕСК', 'СПОРТ', 'СТРОИТЕЛЬ', 'ТРАНСПОРТ', 'ВОДОКАНАЛ', 'ЖИЛИЩ', 'ЗДРАВООХРАНЕНИЯ' ]
list_of_products = ['инвалид', 'питани', 'ремонт', 'лекарств', 'топлив', 'анцеляр', 'бензин', 'мебел', 'Лекарств' ,'сельско']
root_url='https://zakupki.gov.ru'
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'}


class ImpatientHTTPAdapter(requests.adapters.HTTPAdapter):
    """Custom HTTP adapter with timeout option"""
    def __init__(self, timeout=None, *args, **kwargs):
        self.timeout = timeout
        super(ImpatientHTTPAdapter, self).__init__(*args, **kwargs)
    def send(self, *args, **kwargs):
        kwargs['timeout'] = self.timeout
        return super(ImpatientHTTPAdapter, self).send(*args, **kwargs)


class ServerSession(requests.Session):
    """HTTP connection wrapper with pre-set settings"""
    def __init__(self, url_base=None, *args, **kwargs):
        super(ServerSession, self).__init__(*args, **kwargs)
        self.url_base = url_base
    def request(self, method, url, **kwargs):
        absolute_url = self.url_base + url
        return super(ServerSession, self).request(
            method, absolute_url, **kwargs)


def get_api_requester():
    session = ServerSession(root_url)
    #     session.auth = (ENV('API_USER'), ENV('API_PASSWORD'))
    session.mount('http://', ImpatientHTTPAdapter(HTTP_TIMEOUT))
    session.mount('https://', ImpatientHTTPAdapter(HTTP_TIMEOUT))
    return session


def get_data(url):
    # """get page from url"""
    global api
    if api is None:
        api = get_api_requester()
    resp = api.get(url,headers=headers)
    if resp.status_code == 200:
        html_cod_dirty = resp.text.encode('utf-8')
        soup = bs(html_cod_dirty, "lxml")
        return soup


def get_url(numpage):
    url_start = '/epz/order/extendedsearch/results.html?searchString=разработка+программного+обеспечения&morphology=on&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D0%BE%D0%B1%D0%BD%D0%BE%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D1%8F&pageNumber='
    url_finish = '&sortDirection=false&recordsPerPage=_100&showLotsInfoHidden=false&savedSearchSettingsIdHidden=&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&placingWayList=&selectedLaws=&priceFromGeneral=&priceFromGWS=&priceFromUnitGWS=&priceToGeneral=&priceToGWS=&priceToUnitGWS=&currencyIdGeneral=-1&publishDateFrom=&publishDateTo=&applSubmissionCloseDateFrom=&applSubmissionCloseDateTo=&customerIdOrg=&customerFz94id=&customerTitle=&okpd2Ids=&okpd2IdsCodes='
    url = url_start + str(numpage) + url_finish
    return url


def isinSubcompany(company):
    for substring in list_of_company:
        if substring in company:
            return True
            break


def isinSubproduct(product):
    for substring in list_of_products:
        if substring in product:
            return True
            break


def get_lots(amount):
    results = []
    for numpage in range(1, amount):
        url = get_url(numpage)
        soup = get_data(url)
        blocks = soup.find_all('div', class_ = 'search-registry-entry-block')
        for block in blocks:
            company = block.find('div', class_='registry-entry__body-href').text.strip()
            if isinSubcompany(company):
                continue
            else:
                product = block.find('div', class_="registry-entry__body-value").text.strip()
                if isinSubproduct(product):
                    continue
                else:
                    link_product = block.find('div', class_='registry-entry__header-mid__number').find('a').get('href') or ''
                    link_company = block.find('div', class_='registry-entry__body-href').find('a').get('href') or ''
                    # dates = block.find_all('div', class_="data-block__value")
                    # date_added = dates[0].text.strip()
                    # try:
                    #      deadline = dates[2].text.strip()
                    # except IndexError:
                    #      deadline = 'unknown'
                    price_dirty = block.find('div', class_='price-block__value').text.strip()[0:-5]
                    price = float(re.sub("[^0-9]", "", price_dirty)) or 0
                    # status = block.find('div', class_="registry-entry__header-mid__title text-normal").text.strip()
                    # sleep(1)
                    # adress=get_link_company(link_company) or ''
                    # results.append([company, root_url+link_company, adress, product, date_added, deadline, price, status])
                    results.append([company, root_url+link_company,product, price, root_url+link_product])
    return sorted(results, key=lambda result: result[0])


def get_link_company(link_company):
    soup = get_data(link_company)
    adress = soup.find('div', class_='registry-entry__body-block').find('div', class_='registry-entry__body-value').text.strip()
    return adress


def view(amount):
    lots = get_lots(amount)
    with open('zapros2.txt', 'w', encoding='utf-8') as fp:
        json.dump(lots, fp, ensure_ascii=False, indent=4)


view(amount)