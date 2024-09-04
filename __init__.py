import sqlite3
import os

from dotenv import load_dotenv

load_dotenv()

con = sqlite3.connect("pzkids.db")
cur = con.cursor()
n8n_webhook = os.getenv('N8N_WEBHOOK')
class_number = os.getenv('CLASS_NUMBER')
account = os.getenv('ACCOUNT')
phone = os.getenv('PHONE')

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36",
    "Referer": "https://pzkids.bnet.tw/",
}
base_url = "https://pzkids.bnet.tw"