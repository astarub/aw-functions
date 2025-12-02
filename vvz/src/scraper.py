
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time , re , json
import traceback

from appwrite.client import Client
from appwrite.services.databases import Databases 
from datetime import datetime

import os

PROGRESS_FILE = "progress.txt"

# Bereits gespeicherte Kurse laden
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
       done_courses = set(line.strip() for line in f if line.strip())
else:
   done_courses = set()
   
APPWRITE_ENDPOINT = "https://api-dev-app.asta-bochum.de/v1"
PROJECT_ID = "campus_app"
API_KEY = "standard_e4abd7e30c1178a41b4340fd40a30edcf0d2cedc5e5cb4cf4fc57762257435044b07d298e3c5139ad0df3ca6af08971350a2a6176a72782d9b67ddcdd7fc6d1093d5d9b72db1ed21390452bf7ec338b092fba2a8c3bb5bc2e92103518754dffe85e4bdf6f9ab38ecbcd46cd55ede2128ad1bd11e2e59cc028412ed63edcb1daa"
DATABASE_ID = "courses"
COLLECTION_ID = ""

FACULTY_COLLECTIONS = {
    "I.":  "68ff4371002b37d0785c",      # Evangelisch-Theologische Fakultät
    "II.": "69024b840015bdc729d8",       # Katholisch-Theologische Fakultät
    "III.": "6907ab8900018027e6e0",     # Fakultät für Philosophie und Erziehungswissenschaft
    "IV.": "6907df0b000832908ded",       # Fakultät für Geschichtswissenschaft
    "V.": "690908e2000b559395bb",         # Fakultät für Philologie
    "VI.": "690938f100160232c270",      # Juristische Fakultät
    "VIII.": "69093939003a6bb8c995",     # Fakultät für Sozialwissenschaft
    "VII.": "6909392b001c4f530c4a",    # Fakultät für Wirtschaftswissenschaft
    "IX.": "690939530003f03086f2",     # Fakultät für Ostasienwissenschaft
    "X.": "690939aa0031228ba3e2",       # Fakultät für Sportwissenschaft
    "XI.": "69093b05001a55bb235f",      # Fakultät für Psychologie
    "XII.": "69093b23001315a99b29",     # Fakultät für Bau- und Umweltingenieurwissenschaften
    "XIII.": "69093b5e000863a43a2c",    # Fakultät für Maschinenbau
    "XIV.": "69093b8b003b8a9295d4",     # Fakultät für Elektrotechnik und Informationstechnik
    "XV.": "69093bb200383849e0ad",      # Fakultät für Mathematik
    "XVI.": "69093bcb0003eff326d7",      # Fakultät für Physik und Astronomie
    "XVII.": "69093be4000d2adc74c9",    # Fakultät für Geowissenschaften
    "XIX.": "69093bfd002faa70dae0",   # Fakultät für Biologie und Biotechnologie
    "XX.": "69093c15001f6a1b1db5",     # Medizinische Fakultät
    "XXI.": "69093c340021e62e4273",      # Fakultät für Informatik
    "XVIII.": "691b83300017df2f3c8e",     # Fakultät für Chemie und Biochemie
}


# Appwrite Client einrichten
client = Client()
client.set_endpoint(APPWRITE_ENDPOINT)
client.set_project(PROJECT_ID)
client.set_key(API_KEY)

db = Databases(client)


def fetch_html(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[WARN] Fehler beim Laden von {url}: {e}")
        return ""  



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


#als Array speichern
def clean_lecturers(cell):
    names = [n.strip() for n in cell.stripped_strings if n.strip()]
    return names               



def list_courses(eventlist_url: str, module_title: str | None = None):

    courses = []
    current_url = eventlist_url

    while True:
        print(f"[INFO] Lade Kursseite: {current_url}")

        html = fetch_html(current_url)
        soup = BeautifulSoup(html, "html.parser")

        tables = soup.find_all("tbody", class_="tablecontent")
        if not tables:
            break

       
        for tbody in tables:
            number_cells = tbody.find_all(
                "td",
                id=re.compile(r"cas-table_EVENTLIST_COURSENUMBER_\d+")
            )

            for num_cell in number_cells:
                tr = num_cell.find_parent("tr")
                if not tr:
                    continue

                match = re.search(r"_(\d+)$", num_cell.get("id", ""))
                if not match:
                    continue
                idx = match.group(1)

                course_id = (
                    num_cell.find("a").get_text(strip=True)
                    if num_cell.find("a")
                    else num_cell.get_text(" ", strip=True)
                )

                link_tag = num_cell.find("a")
                detail_url = urljoin(current_url, link_tag["href"]) if link_tag else None

                title_td = tr.find("td", id=f"cas-table_EVENTLIST_TITLE_{idx}")
                lecturer_td = tr.find(id=f"cas-table_EVENTLIST_LECTURER_{idx}")
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

     
        # Pagination – nächste Seite finden
       
        next_button = soup.find("a", {"title": "Nächste Seite"})

        if not next_button:
            print("[DONE] Keine nächste Seite.")
            break

        next_href = next_button.get("href")
        if not next_href:
            break

        next_url = urljoin(current_url, next_href)

        # WICHTIG: Endlosschleife verhindern (VVZ-BUG → page=7 wiederholt sich)
        if next_url == current_url:
            print("[STOP] Pagination wiederholt sich Ende erreicht.")
            break

        # → nächste Seite
        current_url = next_url

    return courses


def scrape_items(url, path=None):
    if path is None:
        path = []

    html = fetch_html(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    
    #  FALL 1: eventlist.asp -> Kursliste scrapen
    
    if "eventlist.asp" in url:

        # Modulname festlegen
        if len(path) > 1:
            module_name = path[-1]  
        else:
            module_name = path[0]

        print(f"\n  Modul: {module_name}")

        courses = list_courses(url, module_title=module_name)

        # Kurse anzeigen + speichern
        if not courses:
            print(f"   [INFO] Keine Kurse gefunden in {module_name}")
        else:
            for c in courses:
                course_id = c.get("course_id", "").strip()

                if course_id in done_courses:
                    print(f"[SKIP] Kurs {course_id} bereits gespeichert.")
                    continue

                print(f"     | {c['course_id']} | {c['title']} | {c['lecturers']} | {c['type']}")
                save_course_to_appwrite(c)

        
        result_list = []
        result_list.extend(courses)
        return result_list


   
    #fields.asp / subfields.asp -> Unterseiten
    
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

        # Pfad aktualisieren
        if path and path[-1] == text:
            new_path = path
        else:
            new_path = path + [text]

        # Rekursion — Unterseite scrapen
        sub_results = scrape_items(full_url, new_path)
        results.extend(sub_results)

        time.sleep(0.2)

    return results

    



def scrape_course_details(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    base_data = {}
    for row in soup.select("div.templatecomponent.collapsible div.cas-info-row"):
        label = row.find("div", class_="cas-info-label")
        value = row.find("div", class_="cas-info-value")
        if label and value:
            key = label.get_text(strip=True).replace(":", "")
            val = value.get_text(" ", strip=True)
            base_data[key] = val

    termine = []
    time_infos = []
    seen_dates = set()

    table = soup.find("table", id="appointmentlist")
    if table:
        tbody = table.find("tbody", class_="tablecontent")
        current_header = None

        for tr in tbody.find_all("tr"):
            text = tr.get_text(" ", strip=True)
            if not text or "Termine" in text:  # Störzeilen ignorieren
                continue

            # Kopfzeile -> neuer Block
            m = re.match(r"^([A-Za-zÄÖÜäöü]+),\s*(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2}),\s*(.+)$", text)
            if m:
                current_header = {
                    "weekday": m.group(1),
                    "start": m.group(2),
                    "end": m.group(3),
                    "room": m.group(4),
                }
                time_infos.append(f"{current_header['weekday']} {current_header['start']}-{current_header['end']} | {current_header['room']}")
                continue

            # Datumszeilen auslesen
            dates = re.findall(r"\b\d{2}\.\d{2}\.\d{4}\b", text)
            for date in dates:
                if date not in seen_dates:  # Dubletten vermeiden
                    seen_dates.add(date)
                    if current_header:
                        termine.append({
                            "datum": date,
                            "wochentag": current_header["weekday"],
                            "start": current_header["start"],
                            "ende": current_header["end"],
                            "raum": current_header["room"]
                        })
                    else:
                        termine.append({"datum": date})

    # Termine nach Datum sortieren
    termine.sort(key=lambda x: datetime.strptime(x["datum"], "%d.%m.%Y"))

    time_info = "; ".join(time_infos)
    return {
        "basisdaten": base_data,
        "termine": termine,
    } 




def save_course_to_appwrite(course,COLLECTION_ID):
    
    lecturers_list = course.get("lecturers", [])
    if isinstance(lecturers_list, str):
        lecturers_list = [lecturers_list]

    termine_raw = course.get("termine", [])
    termine_list = []

    for t in termine_raw:
        if isinstance(t, dict):
            # Formatieren in String
            w = t.get("wochentag", "")
            d = t.get("datum", "")
            s = t.get("start", "")
            e = t.get("ende", "")
            r = t.get("raum", "")
            termine_list.append(f"{w} {d} {s}-{e} | {r}".strip())
        else:
            termine_list.append(str(t))

    payload = {
        "course_id": course.get("course_id", ""),
        "title": course.get("title", ""),
        "module": course.get("module", ""),
        "lecturers": lecturers_list,
        "type": course.get("type", ""),
        "termine": termine_list,
        "details_url": course.get("details_url", "")

        
    }

    print("\n[UPLOAD] →", payload["course_id"], payload["title"], payload["termine"])

    try:
        res = db.create_document(
            database_id=DATABASE_ID,
            collection_id=COLLECTION_ID,
            document_id="unique()",
            data=payload
        )
        print(f" Gespeichert: {res['$id']} - {payload['title']}")
    
        # Fortschritt dauerhaft speichern
        course_id = payload["course_id"]
        with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
            f.write(course_id + "\n")
        done_courses.add(course_id)
    except Exception as e:
        print(f"Fehler beim Speichern: {e}")



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
#faculties = faculties[0:1]  
all_courses = []

for fac_name, fac_url in faculties:
    print(f"\n====== {fac_name} ======")

    # 1️⃣ Fakultätskürzel extrahieren (z. B. "XIV.")
    fac_short = fac_name.split()[0]  # NICHT .replace(".") !!

    # 2️⃣ Automatisch die richtige Collection-ID wählen
    if fac_short not in FACULTY_COLLECTIONS:
        print("[ERROR] Unbekannte Fakultät:", fac_short)
        continue

    COLLECTION_ID = FACULTY_COLLECTIONS[fac_short]
    print("[INFO] → Verwende Collection:", COLLECTION_ID)

    # 3️⃣ Progress-Datei pro Fakultät
    #PROGRESS_FILE = f"progress_{fac_short}.txt"
    PROGRESS_FILE = f"progress_{fac_short.replace('.', '')}.txt"


    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            done_courses = set(line.strip() for line in f if line.strip())
    else:
        done_courses = set()

    # 4️⃣ Jetzt scrapen
    courses = scrape_items(fac_url, [fac_name])
    all_courses.extend(courses)


# JSON-Ausgabe
print(json.dumps(all_courses, indent=2, ensure_ascii=False))



for course in all_courses:
    course_id = course.get("course_id", "")
    if course_id in done_courses:
        print(f"[SKIP] {course_id} bereits gespeichert.")
        continue

    save_course_to_appwrite(course, COLLECTION_ID)








