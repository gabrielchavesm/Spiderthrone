from typing import Any

import requests
from bs4 import BeautifulSoup


def scrape_dgsi_ruling(url: str) -> dict[str, Any]:
    response = requests.get(url)
    response.raise_for_status()

    # 1. Descodificamos explicitamente os bytes para texto usando o padrão do governo (windows-1252)
    # antes de passar para o BeautifulSoup, ignorando qualquer meta-tag errada do site.
    html_text = response.content.decode("windows-1252", errors="replace")

    soup = BeautifulSoup(html_text, "html.parser")

    metadata = {
        "source_url": url,
        "court": "",
        "date": "",
        "rapporteur": "",
        "descriptors": "",
    }

    rows = soup.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 2:
            label = cells[0].get_text(strip=True).lower()
            value = cells[1].get_text(strip=True)

            if "tribunal" in label:
                metadata["court"] = value
            # 2. Pesquisa segura: removemos a dependência de acentos na palavra "acórdão"
            elif "data do ac" in label:
                metadata["date"] = value
            elif "relator" in label:
                metadata["rapporteur"] = value
            elif "descritores" in label:
                metadata["descriptors"] = value

    text_blocks = [
        p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)
    ]
    full_text = "\n".join(text_blocks)

    document = {"metadata": metadata, "raw_text": full_text}

    return document
