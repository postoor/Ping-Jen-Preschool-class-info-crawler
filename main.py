import os
import requests
import sqlite3
import json

from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

cookies = os.getenv('COOKIES')
n8n_webhook = os.getenv('N8N_WEBHOOK')

if not cookies:
    raise ValueError('Cookie not found in environment variables')

headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36',
         'Referer': 'https://pzkids.bnet.tw/'}

base_url = "https://pzkids.bnet.tw"
cookie_dict = {}

for cookie in cookies.split(';'):
    name, value = cookie.split('=', 1)
    cookie_dict[name] = value

con = sqlite3.connect("pzkids.db")
cur = con.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS article(name, link, created_at);")
cur.execute("CREATE TABLE IF NOT EXISTS contact_book(date, data, created_at);")


# Photo
# /photo/89
photo_index_body = requests.get(f"{base_url}/classinfo/photo/89", headers=headers, cookies=cookie_dict)

if photo_index_body.status_code != 200:
    raise Exception("Failed to fetch photo index")

soup = BeautifulSoup(photo_index_body.text, "html.parser")
article_image_list = soup.find(id='article-image')

for figure in article_image_list.find_all('figure'):
    article_link = figure.find('a')
    article_name = figure.find('h2').text.strip()
    print({"link": article_link['href'], "name": article_name})
    cur.execute("SELECT * FROM article WHERE name = ?", (article_name,))
    row = cur.fetchone()
    if row:
        print(f"Article {article_name} already exists")
        continue

    photo_dir = f"./files/photo/{article_name}"
    os.makedirs(photo_dir, exist_ok=True)

    article = requests.get(f"{base_url}/{article_link['href']}", headers=headers, cookies=cookie_dict)
    photo_list = BeautifulSoup(article.text, "html.parser").find(id='container').find_all('img')
    for photo in photo_list:
        print(photo['src'])
        photo_type = photo['src'].split('.')[-1]
        photo_name = photo['alt']
        with open(f"{photo_dir}/{photo_name}.{photo_type}", 'wb') as fp:
            response = requests.get(photo['src'], headers=headers, cookies=cookie_dict)
            fp.write(response.content)
        fp.close()
    cur.execute("INSERT INTO article(name, link, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)", (article_name, article_link['href']))
    con.commit()

# Contact Book
# /contactbook/89
contact_book_body = requests.get(f"{base_url}/classinfo/contactbook/89", headers=headers, cookies=cookie_dict)
soup = BeautifulSoup(contact_book_body.text, "html.parser")
contact_info = soup.find('div', class_='contactbook').find('div')
contact_info_list = []
date = contact_info.find('h3').text.strip().split(" ")[-2].split('/')[-1].strip()
cur.execute("SELECT * FROM contact_book WHERE date = ?", (date, ))
row = cur.fetchone()

if row:
    print(f"Contact book for {date} already exists")
else:
    for contact in contact_info.find_all('div', class_="cbbox"):
        
        title = contact.find('div', class_="title").text.strip("：").strip()
        desc_element = contact.find('div', class_="desc")
        desc_file_element = contact.find('div', class_="descfiles")
        desc = desc_element.text.strip() if desc_element else ""

        contact_info_list.append({"title": title, "desc": desc})
        
        if desc_file_element:
            os.makedirs(f"./files/contact_book/{date}", exist_ok=True)
            for file_link_element in desc_file_element.find_all('a'):
                file_link = file_link_element['href']
                file_name = file_link.split('/')[-1]
                with open(f"./files/contact_book/{date}/{file_name}", 'wb') as fp:
                    response = requests.get(file_link, headers=headers, cookies=cookie_dict)
                    fp.write(response.content)
                fp.close()
    contact_string = json.dumps(contact_info_list, ensure_ascii=False)
    cur.execute("INSERT INTO contact_book(date, data, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)", (date, contact_string,))
    con.commit()
    if n8n_webhook:
        requests.post(n8n_webhook, json={item['title']: item['desc'] for item in contact_info_list})
con.close()
