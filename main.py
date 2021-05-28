from selenium import webdriver
import pandas as pd
from bs4 import BeautifulSoup as bs
import requests
import re


def get_ebay_item(page_source):
    list_items = []
    source = bs(page_source, 'html.parser')
    lis = source.find_all('li', attrs={'class': 'sresult lvresult clearfix li shic'})
    for li in lis:
        list_items.append(li.get('listingid'))
    return list_items


def get_title(page_source):
    title_tag = bs(page_source, 'html.parser')
    title = title_tag.find('h1', attrs={'id':'itemTitle'}).text
    search = re.search(f'(Details about\s+)(.+)', title)
    return search.group(2)


def get_price(page_source):
    price_tag = bs(page_source, 'html.parser')
    price = price_tag.find('span', attrs={'id':'prcIsum'}).get('content')
    return price


def get_ship(page_source):
    ship_tag = bs(page_source, 'html.parser')
    ship_text = ship_tag.find('div', attrs={'id':'shippingSummary'})
    text = ship_text.text.strip()
    search = re.search(f'\$([0-9.,]+)',text)
    if 'free' in text.lower():
        return 0
    elif search is not None:
        return search.group(1)
    else:
        return 'N/A'


def get_total(page_source):
    total = bs(page_source, 'html.parser')
    price = get_price(page_source)
    ship = get_ship(page_source)
    try:
        total = float(price) + float(ship)
    except:
        total = float(price)
    return total


def get_sold(page_source):
    sold_tag = bs(page_source, 'html.parser')
    try:
        sold_field = sold_tag.find('div', attrs={'id':'why2buy'})
        text_sold = sold_field.text.strip()
        get_sold = re.search(f'([0-9,]+)(\sSold)', text_sold)
        sold = get_sold.group(1).replace(',', '')
        return sold
    except:
        sold_field = sold_tag.find('a', attrs={'class':'vi-txt-underline'})
        get_sold = re.search(f'([0-9,]+)(\sSold)', sold_field.text, flags=re.IGNORECASE)
        return get_sold.group(1)


def get_description(page_source):
    des_tag = bs(page_source)
    des = des_tag.find('div', attrs={'id':'desc_div'})
    src = des.iframe.get('src')
    response = requests.get(src)
    html = bs(response.text, 'html.parser')
    div = html.find('div', attrs={'id':'ds_div'})
    text = div.text.strip()
    return text.replace('\xa0', '')


def get_images(driver):
    list_img = []
    while True:
        page = driver.page_source
        page = bs(page, 'html.parser')
        img = page.find('img', attrs={'id':'icImg'}).get('src')
        list_img.append(img)

        try:
            driver.find_element_by_xpath("//button[@class='next-arr navigation-image-arr']").click()
        except:
            break
        
    return list_img


url = input('Input your search page:\n')
url_check = re.search(f'ebay\.([a-z]+)', url)
domain = url_check.group(1)
driver_path = 'chromedriver.exe'
pattern = url + '&_pgn={}&_skc={}&rt=nc'
list_items = []
url_item = 'https://www.ebay.{}/itm/'.format(domain)
result = []


if __name__ == '__main__':
    driver = webdriver.Chrome(driver_path)
    driver.get(url)
    input('Waiting for change location! Then press ENTER key to continue\n')
    page_source = driver.page_source

    print('\nStarting now ...')

    while True:
        page_source = driver.page_source
        list_items.append(get_ebay_item(page_source))
        try:
            new_url = bs(page_source, 'html.parser').find('a', attrs={'class': 'gspr next'})
            driver.get(new_url.get('href'))
        except:
            break

    list_items = sum(list_items, [])
    quantity = len(list_items)
    index = 0

    for item in list_items:
        index += 1
        print(f'Getting info {index}/{quantity} items')

        driver.get(url_item+item)
        page = driver.page_source

        item_number = item
        title = get_title(page)
        price = get_price(page)
        ship = get_ship(page)
        total_price = get_total(page)
        sold = get_sold(page)
        description = get_description(page)
        images = get_images(driver)

        assign = ['N/A']*10
        for i in range(len(images)):
            try:
                assign[i] = images[i]
            except:
                break

        result.append({'item': item,
                       'title': title,
                       'price': price,
                       'ship': ship,
                       'total_price': total_price,
                       'sold': sold,
                       'description': description,
                       'image_1': assign[0],
                       'image_2': assign[1],
                       'image_3': assign[2],
                       'image_4': assign[3],
                       'image_5': assign[4],
                       'image_6': assign[5],
                       'image_7': assign[6],
                       'image_8': assign[7],
                       'image_9': assign[8],
                       'image_10': assign[9]})

    df = pd.DataFrame(result)
    df.to_excel('result.xlsx')

    print('COMPLETED!')