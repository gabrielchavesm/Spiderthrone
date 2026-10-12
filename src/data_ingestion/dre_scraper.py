import re
from typing import Any

from playwright.sync_api import sync_playwright


def scrape_dre_law(url: str) -> dict[str, Any]:
    # Inicia o motor do Playwright
    with sync_playwright() as p:
        # Lança um Google Chrome invisível (headless)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Waiting for DRE's JavaScript to render the page...")

        # Navega para o site e espera até que o tráfego de rede acalme (garantindo que o JS terminou de ler a base de dados)
        page.goto(url, wait_until="networkidle")

        # Espera obrigatoriamente que o título apareça no ecrã para prosseguir
        page.wait_for_selector("h1", timeout=15000)

        metadata = {
            "source_url": url,
            "law_title": "Unknown Title",
            "date": "01-01-1900",
        }

        # Extrai o Título
        title_element = page.query_selector("h1")
        if title_element:
            metadata["law_title"] = title_element.inner_text().strip()

        # Extrai a Data (Procurando na página inteira renderizada)
        page_text = page.locator("body").inner_text()
        date_pattern = r"\b(\d{4}-\d{2}-\d{2}|\d{2}-\d{2}-\d{4})\b"
        date_matches = re.findall(date_pattern, page_text)

        if date_matches:
            metadata["date"] = date_matches[0]

        # Extrai o Texto
        text_blocks = []

        # O DRE usa frequentemente estes IDs/classes para o corpo da lei
        elements = page.locator("#texto-diploma p, .texto-diploma p, article p")

        # Se os seletores falharem, caçamos todos os parágrafos da página como plano B
        if elements.count() == 0:
            elements = page.locator("p")

        # O all_inner_texts() do Playwright extrai instantaneamente todo o texto limpo
        texts = elements.all_inner_texts()

        for text in texts:
            clean_text = text.strip()
            if len(clean_text) > 30 and clean_text not in text_blocks:
                text_blocks.append(clean_text)

        full_text = "\n".join(text_blocks)

        document = {"metadata": metadata, "raw_text": full_text}

        # Fecha o navegador para não gastar memória RAM
        browser.close()

        return document


if __name__ == "__main__":
    test_url = "https://diariodarepublica.pt/dr/detalhe/decreto-lei/269-1998-566629"
    print("Starting Headless Browser (Playwright)...")

    scraped_data = scrape_dre_law(test_url)

    print("\n--- DRE SCRAPER RESULTS ---")
    print(f"Title: {scraped_data['metadata']['law_title']}")
    print(f"Date found: {scraped_data['metadata']['date']}")
    print(f"\nText snippet:\n{scraped_data['raw_text'][:400]}...")
