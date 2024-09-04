import requests
import json
import sqlite3
import os

from __init__ import (
    cur,
    n8n_webhook,
    class_number,
    account,
    phone,
    headers,
    base_url,
    con,
)
from bs4 import BeautifulSoup

session = requests.session()

login_payload = {"account": account, "phone": phone}
login = session.post(
    f"{base_url}/wapp/index/prochk", headers=headers, data=login_payload
)

if login.status_code != 200:
    raise Exception("Failed to login")


def init_db(cur: sqlite3.Cursor):
    cur.execute("CREATE TABLE IF NOT EXISTS article(name, link, created_at);")
    cur.execute("CREATE TABLE IF NOT EXISTS contact_book(date, data, created_at);")


init_db(cur)

photo_index_body = session.get(f"{base_url}/classinfo/photo/{class_number}")
if photo_index_body.status_code != 200:
    raise Exception("Failed to fetch photo index")

soup = BeautifulSoup(photo_index_body.text, "html.parser")
article_image_list = soup.find(id="article-image")

for figure in article_image_list.find_all("figure"):
    article_link = figure.find("a")
    article_name = figure.find("h2").text.strip()
    print({"link": article_link["href"], "name": article_name})
    cur.execute("SELECT * FROM article WHERE name = ?", (article_name,))
    row = cur.fetchone()
    if row:
        print(f"Article {article_name} already exists")
        continue

    photo_dir = f"./files/photo/{article_name}"
    os.makedirs(photo_dir, exist_ok=True)

    article = session.get(f"{base_url}/{article_link['href']}")
    photo_list = (
        BeautifulSoup(article.text, "html.parser").find(id="container").find_all("img")
    )
    for photo in photo_list:
        print(photo["src"])
        photo_type = photo["src"].split(".")[-1]
        photo_name = photo["alt"]
        with open(f"{photo_dir}/{photo_name}.{photo_type}", "wb") as fp:
            response = session.get(photo["src"])
            fp.write(response.content)
        fp.close()
    cur.execute(
        "INSERT INTO article(name, link, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
        (article_name, article_link["href"]),
    )
    con.commit()

# Contact Book
# /contactbook/{class_number}
contact_book_body = session.get(f"{base_url}/classinfo/contactbook/{class_number}")
soup = BeautifulSoup(contact_book_body.text, "html.parser")
contact_info = soup.find("div", class_="contactbook").find("div")
contact_info_list = []
date = contact_info.find("h3").text.strip().split(" ")[-2].split("/")[-1].strip()
cur.execute("SELECT * FROM contact_book WHERE date = ?", (date,))
row = cur.fetchone()

if row:
    print(f"Contact book for {date} already exists")
else:
    for contact in contact_info.find_all("div", class_="cbbox"):

        title = contact.find("div", class_="title").text.strip("：").strip()
        desc_element = contact.find("div", class_="desc")
        desc_file_element = contact.find("div", class_="descfiles")
        desc = desc_element.text.strip() if desc_element else ""

        contact_info_list.append({"title": title, "desc": desc})

        if desc_file_element:
            os.makedirs(f"./files/contact_book/{date}", exist_ok=True)
            for file_link_element in desc_file_element.find_all("a"):
                file_link = file_link_element["href"]
                file_name = file_link.split("/")[-1]
                with open(f"./files/contact_book/{date}/{file_name}", "wb") as fp:
                    response = session.get(f"{base_url}{file_link}")
                    fp.write(response.content)
                fp.close()
    contact_string = json.dumps(contact_info_list, ensure_ascii=False)
    cur.execute(
        "INSERT INTO contact_book(date, data, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
        (
            date,
            contact_string,
        ),
    )
    con.commit()
    if n8n_webhook:
        requests.post(
            n8n_webhook,
            json={item["title"]: item["desc"] for item in contact_info_list},
        )
con.close()
