import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time , re , json

def get_rendered_html(url, wait=3):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        time.sleep(wait)
        html = driver.page_source
    finally:
        driver.quit()
    return html


start_url = "https://vvz.ruhr-uni-bochum.de/campus/all/fields.asp?group=Vorlesungsverzeichnis&lang=de"

# Fakultäten erkennen
roman_re = re.compile(r'^([IVXLCDM]+)\.')
def is_faculty(text: str) -> bool:
    return bool(roman_re.match(text)) and "Fakultät" in text

def roman_order(name: str) -> int:
    order = ["I.","II.","III.","IV.","V.","VI.","VII.","VIII.","IX.","X.",
             "XI.","XII.","XIII.","XIV.","XV.","XVI.","XVII.","XVIII.","XIX.","XX.","XXI."]
    m = roman_re.match(name.strip())
    token = (m.group(1) + '.') if m else 'ZZZ.'
    return order.index(token) if token in order else 999


def clean_lecturers(td):
    # Zerlegt den Text an Zeilenumbrüchen (z.B. <br>), entfernt leere Einträge
    if not td:
        return ""
    parts = [p.strip() for p in td.stripped_strings if p.strip()]
    return " ; ".join(parts)



 
def list_courses(eventlist_url: str, module_title: str | None = None):
    #print(f"[DEBUG] RENDER mit Selenium: {eventlist_url}")
    html = get_rendered_html(eventlist_url)
    #print(f"[DEBUG] Länge HTML: {len(html)}")
    soup = BeautifulSoup(html, "html.parser")



    tables = soup.find_all("tbody", class_="tablecontent")
    if not tables:
        return []

    courses = []

    #  ALLE Tabellen der Seite durchlaufen
    for tbody in tables:
        number_cells = tbody.find_all("td", id=re.compile("cas-table_EVENTLIST_COURSENUMBER_\\d+"))
        for num_cell in number_cells:
            tr = num_cell.find_parent("tr")
            if not tr:
                continue

            # Index aus ID holen
            match = re.search(r"_(\d+)$", num_cell.get("id", ""))
            if not match:
                continue
            idx = match.group(1)

            # Daten wie gewohnt auslesen
            course_id = num_cell.get_text(" ", strip=True)
            link_tag = num_cell.find("a")
            detail_url = urljoin(eventlist_url, link_tag["href"]) if link_tag else None

            title_td = tr.find("td", id=f"cas-table_EVENTLIST_TITLE_{idx}")
            lecturer_td = tr.find("td", id=f"cas-table_EVENTLIST_LECTURER_{idx}")
            type_td = tr.find("td", id=f"cas-table_EVENTLIST_SWS_{idx}")

            title = title_td.get_text(" ", strip=True) if title_td else ""
            lecturers = clean_lecturers(lecturer_td)
            type_ = type_td.get_text(" ", strip=True) if type_td else ""

            details = scrape_course_details(detail_url) if detail_url else {"basisdaten": {}, "termine": []}

            courses.append({
                "module": module_title,
                "course_id": course_id,
                "title": title,
                "lecturers": lecturers,
                "type": type_,
                "details_url": detail_url,
                "basisdaten": details.get("basisdaten"),
                "termine": details.get("termine")
            })

    return courses


    

def scrape_course_details(url):
    try:
        r = requests.get(url, timeout=10)   # statt 30
        r.raise_for_status()
    except Exception as e:
        print(f"[WARN] Detailseite konnte nicht geladen werden: {url} ({e})")
        return {"basisdaten": {}, "termine": []}


visited = set()

""" def scrape_items(url, path=None):
    if path is None:
        path = []

    if url in visited:
        return []
    visited.add(url)

    try:
        html = get_rendered_html(url)
    except Exception as e:
        print(f"[WARN] Fehler bei {url}: {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")

    # === Fall 1: Kursliste (eventlist.asp) ===
    if "eventlist.asp" in url:
        module_name = " > ".join(path)
        print(f"\n  Modul: {module_name}")
        courses = list_courses(url, module_title=module_name)
        for c in courses:
            print(f"     | {c['course_id']} | {c['title']} | {c['lecturers']} | {c['type']}")
            if c.get("termine"):
                for t in c["termine"]:
                    wochentag = t.get("wochentag", "")
                    start = t.get("start", "")
                    ende = t.get("ende", "")
                    raum = t.get("raum", "")
                    datum = t.get("datum", "")
                    print(f"          {wochentag} {start}–{ende} @ {raum} ({datum})")
        return courses

    # === Fall 2: Untermodul-Liste (subfields.asp oder fields.asp) ===
    tbody = soup.find("tbody", class_="tablecontent")
    if not tbody:
        return []

    results = []
    for a in tbody.find_all("a"):
        text = a.get_text(strip=True)
        href = a.get("href") or ""
        if not text or not href:
            continue
        if href.startswith("#") or href.lower().startswith("javascript:"):
            continue

        full_url = urljoin(url, href)

        # Rekursion → gehe tiefer
        results.extend(scrape_items(full_url, path + [text]))
        time.sleep(0.2)

    return results """

def scrape_items(url, path=None):
    if path is None:
        path = []

    if url in visited:
        return []
    visited.add(url)

    try:
        html = get_rendered_html(url)
    except Exception as e:
        print(f"[WARN] Fehler bei {url}: {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")

    # === Fall 1: Kursliste (eventlist.asp) ===
    if "eventlist.asp" in url:
        module_name = " > ".join(path)
        if len(path)==1:
            return []
        print(f"\n  Modul: {module_name}")
        courses = list_courses(url, module_title=module_name)
        
        for c in courses:
            print(f"     | {c['course_id']} | {c['title']} | {c['lecturers']} | {c['type']}")
            if c.get("termine"):
                for t in c["termine"]:
                    wochentag = t.get("wochentag", "")
                    start = t.get("start", "")
                    ende = t.get("ende", "")
                    raum = t.get("raum", "")
                    datum = t.get("datum", "")
                    print(f"          {wochentag} {start}–{ende} @ {raum} ({datum})")
        return courses

    # === Fall 2: Untermodul-Liste (subfields.asp oder fields.asp) ===
    tbody = soup.find("tbody", class_="tablecontent")
    if not tbody:
        return []

    results = []
    for a in tbody.find_all("a"):
        text = a.get_text(strip=True)
        href = a.get("href") or ""
        if not text or not href:
            continue
        if href.startswith("#") or href.lower().startswith("javascript:"):
            continue

        full_url = urljoin(url, href)

        # doppelte Namenswiederholung verhindern
        if path and path[-1] == text:
            new_path = path  # nicht nochmal anhängen
        else:
            new_path = path + [text]

        # Rekursion → gehe tiefer
        results.extend(scrape_items(full_url, new_path))
        time.sleep(0.2)

    return results




def scrape_course_details(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # --- Basisdaten ---
    base_data = {}
    for row in soup.select("div.templatecomponent.collapsible div.cas-info-row"):
        label = row.find("div", class_="cas-info-label")
        value = row.find("div", class_="cas-info-value")
        if label and value:
            key = label.get_text(strip=True).replace(":", "")
            val = value.get_text(" ", strip=True)
            base_data[key] = val

    # Termine 
    termine = []
    table = soup.find("table", id="appointmentlist")
    if table:
        # Oberste Terminzeile mit Wochentag, Uhrzeit, Raum
        header_td = table.select_one("tbody.tablecontent tr td")
        if header_td:
            header_text = header_td.get_text(" ", strip=True)
           
            m = re.match(r"^([A-Za-z]+),\s*([\d:]+)\s*-\s*([\d:]+),\s*(.+)$", header_text)
            if m:
                wochentag = m.group(1)
                startzeit = m.group(2)
                endzeit = m.group(3)
                raum = m.group(4)
            else:
                wochentag = startzeit = endzeit = raum = ""

        #  Einzeltermine → nach dem Header kommen weitere <tr>
        date_rows = table.select("tbody.tablecontent tr")[1:]  # ab 2. Zeile
        for row in date_rows:
            date_text = row.get_text(" ", strip=True)
            if not date_text:
                continue
            termine.append({
                "datum": date_text,
                "wochentag": wochentag,
                "start": startzeit,
                "ende": endzeit,
                "raum": raum
            })

    return {
        "basisdaten": base_data,
        "termine": termine
    }




# Hauptlauf 
r = requests.get(start_url, timeout=30)
r.raise_for_status()
soup = BeautifulSoup(r.text, "html.parser")

faculties = []
seen = set()
for a in soup.find_all("a"):
    text = a.get_text(strip=True)
    href = a.get("href")
    if not text or not href or not is_faculty(text):
        continue
    full_url = urljoin(start_url, href)
    key = (text, full_url)
    if key not in seen:
        seen.add(key)
        faculties.append(key)

faculties.sort(key=lambda x: roman_order(x[0]))
faculties = faculties[:1]  # zum Testen nur die erste Fakultät
all_courses = []

for fac_name, fac_url in faculties:
    print(f"\n====== {fac_name} ======")
    courses = scrape_items(fac_url, [fac_name])
    all_courses.extend(courses)
    

# hier nur zum testen der ersten Ebene also nur name der Fakulitäten mit dennen Links 
"""print("\n====== Fakultäten (Testlauf) ======")
for i, (name, url) in enumerate(faculties):
    print(f"{i+1:02d}. {name} → {url}")"""

# JSON-Ausgabe
print(json.dumps(all_courses, indent=2, ensure_ascii=False))




