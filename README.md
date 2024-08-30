# Pingzhen Kindergarten Parent-Teacher Communication System Crawler

## Features

Crawl information from the communication system and store it in SQLite.

| Feature          | Status               |
| ---------------- | -------------------- |
| Class Announcements | -                  |
| Activity Photos   | △ Currently only captures the first page |
| Activity Videos   | -                    |
| Message Notifications | -              |
| Parent-Teacher Communication Book | △ Currently only captures today's entries |
| Surveys           | -                    |
| Medication Authorization | -           |
| File Downloads    | -                    |
| Webhook           | △ Only sends Parent-Teacher Communication Book entries |

***○ Completed △ Partially Completed - Not Completed***

## Usage

1. After logging in, copy the cookie from the browser into `.env`, following the format in `env.example`.
2. (Optional) Provide the webhook link for n8n.
3. (Optional) Copy the system file to set up a timer.
4. Run `pip install -r requirements.txt`.
5. Execute `python main.py`.