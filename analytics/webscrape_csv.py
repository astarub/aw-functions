import os

import requests
import datetime
import visualize_data

"""
To generate the correct request go to https://analytics.app.asta-bochum.de/5tYPT4xJeGH6zAN4xsSWYv/export, go on 
developer tools (Firefox: F12), go to "Network" (or: Netzwerkanalyse), press on any month and right click the first 
request, copy paste into: https://curlconverter.com/ (there are instructions with pictures as well)
"""

CSV_DATA_DIR = "csv_data"


def send_request_and_write_file(build_mode: str, year: str, month: str) -> None:
    # TODO simply changing build_mode attribute maybe does not work; if there is no result (empty csv; only header) then
    # TODO someone has to recreate the request as described above (and put it into other method)
    """
    :param build_mode: one of "release" or "debug"
    :param year: the year as four-digit number: e.g. 2024
    :param month: the month as number: e.g. 5 (or 05) for May
    """
    if len(month) == 1:
        month = "0" + month

    # GENERATED FROM https://curlconverter.com/ (SEE TOP OF THIS FILE)
    cookies = {
        'auth-session': 'YOUR_SESSION_COOKIE',
        'crisp-client^%^2Fsession^%^2F6a643f4e-c28f-44df-91af-8072159892ea': 'session_4dfed6a9-f9ac-4f3d-90a1-67ee107876ce',
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
        # 'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Connection': 'keep-alive',
        'Referer': 'https://analytics.app.asta-bochum.de/5tYPT4xJeGH6zAN4xsSWYv/export',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Priority': 'u=1',
    }

    params = {
        'appId': '5tYPT4xJeGH6zAN4xsSWYv',
        'appName': 'Campus App',
        'buildMode': build_mode,
        'format': 'csv',
        'year': year,
        'month': month,
    }

    response = requests.get(
        'https://analytics.app.asta-bochum.de/api/_export/download',
        params=params,
        cookies=cookies,
        headers=headers,
    )
    # GENERATED TO HERE

    if not response.status_code == 200:
        raise Exception("Did not get valid response, maybe the cookie timed out")

    # write the csv file
    csv_location = os.path.join(CSV_DATA_DIR, f"campusapp-{build_mode}-{year}-{month}.csv")
    with open(csv_location, "w") as file:
        file.write(response.content.decode())

    # generate png files for the current month
    visualize_data.save_all_as_png(csv_location)


def monthly_request_for_previous_month():
    """
    This method should be called at the beginning of each month to get the results of the previous month
    (Will be called, when the script is run)
    """
    now = datetime.datetime.now()
    year, month = now.year, now.month - 1
    if month == 0:  # in January request for December of the previous year
        year, month = year-1, 12
    send_request_and_write_file("debug", str(year), str(month))


if __name__ == '__main__':
    monthly_request_for_previous_month()
