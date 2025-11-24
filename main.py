print("GraphON-Klops-Parser v0.16")
print("Инициализация библиотек...")
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import requests
import json
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import time

print("Успешно!")


def convert_events_to_json(events, web_page):
    event_categories = {
        "Концерты": "690bff31f371d05b325be7b1",
        "Театр": "690ef8344c94408de5d83d6d",
        "Стендап": "690c0006f371d05b325be7c7",
        "Выставки": "690bffeff371d05b325be7b7",
        "Встречи": "690ef49e4c94408de5d83d4d",
        "Лекции, мастер-классы": "690bfff6f371d05b325be7bb",
        "Вечеринки": "690ef48e4c94408de5d83d47",
        "Кино": "690ef4b14c94408de5d83d53",
        "Спорт": "690c0001f371d05b325be7c3",
    }
    ru_months = {
        "янв": 1,
        "фев": 2,
        "мар": 3,
        "апр": 4,
        "май": 5,
        "мая": 5,
        "июн": 6,
        "июл": 7,
        "авг": 8,
        "сен": 9,
        "сент": 9,
        "окт": 10,
        "ноя": 11,
        "дек": 12,
        "января": 1,
        "февраля": 2,
        "марта": 3,
        "апреля": 4,
        "мая": 5,
        "июня": 6,
        "июля": 7,
        "августа": 8,
        "сентября": 9,
        "октября": 10,
        "ноября": 11,
        "декабря": 12,
    }
    event_list = []

    def to_iso_z(s: str) -> str:
        today = datetime.now(timezone.utc)
        s = s.strip().lower()
        if "-" in s and any(m in s for m in ru_months):
            dt = today.replace(hour=0, minute=0, second=0, microsecond=0)
            return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")
        parts = s.split()
        day = None
        month = None
        hour = 0
        minute = 0
        for i, p in enumerate(parts):
            if p.isdigit():
                day = int(p)
            elif p.rstrip(":").isdigit() and ":" in p:
                pass
            elif p in ru_months:
                month = ru_months[p]
            elif ":" in p:
                hh, mm = p.split(":")[:2]
                hour = int(hh)
                minute = int(mm)
        if day is None or month is None:
            dt = today.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            year = today.year
            dt = datetime(year, month, day, hour, minute, 0, 0, tzinfo=timezone.utc)
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    for event in events:
        event_dict = {}
        event_dict["graphId"] = {"$oid": "690c03a5f371d05b325be7de"}
        event_dict["globalGraphId"] = {"$oid": "690bfec3f371d05b325be7ad"}
        event_dict["parentGraphId"] = {
            "$oid": event_categories[
                event.find("div", class_="card-label").get_text(strip=True)
            ]
        }
        event_dict["name"] = event.find("h4", class_="card-title").get_text(strip=True)
        event_dict["place"] = event.find("div", class_="card-place").get_text(
            strip=True
        )
        event_dict["description"] = (
            BeautifulSoup(
                requests.get(
                    f"https://klops.ru{web_page.find("a", class_="card-item")["href"]}"
                ).text,
                features="html.parser",
            )
            .find("div", class_="detail-description detail-mb")
            .get_text(strip=True)
        )
        event_dict["eventDate"] = {
            "$date": to_iso_z(
                event.find("div", class_="card-date").get_text(strip=True)
            )
        }
        event_dict["isDateTbd"] = False
        event_dict["regedUsers"] = 0
        event_dict["imgPath"] = event.find("div", class_="card-preview").find("img")[
            "src"
        ]
        event_dict["type"] = "city"
        event_list.append(event_dict)

    return event_list


def get_dates():
    now = datetime.now()
    current_date = now.strftime("%d.%m.%Y")
    new_date = now + timedelta(days=7)
    if now.day > 30:
        new_date += relativedelta(months=1)
    elif now.month == 12 and now.day > 30:
        new_date += relativedelta(years=1, months=-11)
    future_date = new_date.strftime("%d.%m.%Y")
    return f"{current_date}-{future_date}"


print("Вызов Chrome и первичный парсинг...")
driver = webdriver.Chrome()
driver.get(f"https://klops.ru/afisha/search?period={get_dates()}")
while True:
    try:
        driver.find_element(By.CLASS_NAME, "btn-theme-next.js-loader").click()
    except:
        break
result = driver.page_source
web_page = BeautifulSoup(result, features="html.parser")
events = [
    i
    for i in web_page.find("div", class_="card-list").find_all("a", class_="card-item")
]
print("Успешно!")
print(f"Количество мероприятий: {len(events)}")

with open("events.json", "w") as f:
    print("Начало создания json файла...")
    a = convert_events_to_json(events, web_page)
    json.dump(a, f, indent=4)
    print("Успешно! Через 5 секунд программа завершится.")
    time.sleep(5)
driver.quit()
