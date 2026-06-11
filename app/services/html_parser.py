import html

from bs4 import BeautifulSoup
from app.models.schemas import ApplicationData


from bs4 import BeautifulSoup

def normalize(text: str) -> str:
    return " ".join(text.replace("\xa0", " ").split())

def build_label_index(soup) -> dict[str, str]:
    index: dict[str, str] = {}

    for td in soup.find_all("td"):
        label_div = td.find("div", class_=lambda c: c in {"label", "boldlabel"})
        data_div = td.find("div", class_="data")

        if not label_div or not data_div:
            continue

        label = normalize(label_div.get_text(" ", strip=True))
        value = data_div.get_text(" ", strip=True)

        index[label] = value

    return index



def get_checked_value_by_label(soup, label_text: str) -> str:
    target = normalize(label_text)

    for label_div in soup.find_all("div", class_=lambda c: c in {"label", "boldlabel"}):
        full_label = normalize(label_div.get_text(" ", strip=True))
        if target not in full_label:
            continue

        container = label_div.find_parent("td")
        if not container:
            return ""

        for row in container.find_all("tr"):
            checkbox = row.find("input", {"type": "checkbox"})
            if checkbox and checkbox.has_attr("checked"):
                value_cell = row.find("td", class_="smalldata")
                return value_cell.get_text(" ", strip=True) if value_cell else ""

        return ""

    return ""

def get_by_label(index: dict[str, str], label_text: str) -> str:
    target = normalize(label_text)

    for label, value in index.items():
        if target in label:
            return value

    return ""

def parse_application_html(html_text: str) -> ApplicationData:
    soup = BeautifulSoup(html_text, "lxml")
    index = build_label_index(soup)

    return ApplicationData(
        ttb_id=get_by_label(index, "TTB ID"),
        plant_registry_basic_permit_brewers_no=get_by_label(index, "2. PLANT REGISTRY/BASIC PERMIT/BREWER'S NO."),
        source_of_product = get_checked_value_by_label(soup, "SOURCE OF PRODUCT"),
        serial_number = get_by_label(index, "SERIAL NUMBER"),
        type_of_product = get_checked_value_by_label(soup, "TYPE OF PRODUCT"),
        brand_name = get_by_label(index, "BRAND NAME"),
        fanciful_name = get_by_label(index, "FANCIFUL NAME"),
        name_and_address = get_by_label(index, "NAME AND ADDRESS"),
        mailing_address = get_by_label(index, "MAILING ADDRESS"),
        email_address = get_by_label(index, "EMAIL ADDRESS"),
        grape_varietal = get_by_label(index, "GRAPE VARIETAL"),
        formula =  get_by_label(index, "FORMULA"),
        net_contents = get_by_label(index, "NET CONTENTS"),
        alcohol_content = get_by_label(index, "ALCOHOL CONTENT"),
        wine_appellation = get_by_label(index, "WINE APPELLATION"),
        wine_vintage_date = get_by_label(index, "WINE VINTAGE DATE"),
        phone_number = get_by_label(index, "PHONE NUMBER"),
        fax_number = get_by_label(index, "FAX NUMBER"),
        date_of_application = get_by_label(index, "DATE OF APPLICATION"),
        type_of_application = get_checked_value_by_label(soup, "TYPE OF APPLICATION"),
        # signature = ""
        print_name_of_applicant = normalize(get_by_label(index, "PRINT NAME OF APPLICANT"),
    )
)
    