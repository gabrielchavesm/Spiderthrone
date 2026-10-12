import csv
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

def harvest_dgsi_mass_engine(target_count=1500):
    """
    Extrai milhares de acórdãos da DGSI percorrendo sequencialmente 
    os blocos numéricos da base de dados do STJ.
    """
    print(f"\n[DGSI] A iniciar extração em massa de até {target_count} acórdãos...")
    base_domain = "https://www.dgsi.pt"
    # URL de listagem geral sem restrições de categoria restritas
    base_url = "https://www.dgsi.pt/jstj.nsf?OpenDatabase"
    
    collected_links = set()
    start_index = 1
    batch_size = 100
    max_loops = (target_count // batch_size) + 5

    for _ in range(max_loops):
        paginated_url = f"https://www.dgsi.pt/jstj.nsf/1?OpenView&Start={start_index}&Count={batch_size}"
        print(f"   -> A recolher bloco a partir do registo {start_index} (Total acumulado: {len(collected_links)})...")
        
        try:
            response = requests.get(paginated_url, timeout=15)
            if response.status_code != 200:
                # Fallback para a base de dados principal se a view 1 falhar
                alt_url = f"{base_url}&Start={start_index}&Count={batch_size}"
                response = requests.get(alt_url, timeout=15)
                
            if response.status_code != 200:
                print("   -> Fim dos blocos acessíveis atingido.")
                break
                
            soup = BeautifulSoup(response.content.decode('windows-1252', errors='replace'), 'html.parser')
            links = soup.find_all('a')
            found_in_batch = 0
            
            for a in links:
                href = a.get('href')
                if href and "OpenDocument" in href:
                    full_url = urljoin(base_domain, href)
                    if full_url not in collected_links:
                        collected_links.add(full_url)
                        found_in_batch += 1
                        
            if found_in_batch == 0:
                break
                
            start_index += batch_size
            time.sleep(0.4) # Pausa técnica de civismo para com o servidor público
            
            if len(collected_links) >= target_count:
                break
                
        except Exception as e:
            print(f"   [AVISO DGSI]: {e}")
            break
            
    return [{"url": link, "type": "DGSI"} for link in collected_links]


def harvest_dre_mass_engine(target_count=500):
    """
    Extrai diplomas do Diário da República simulando navegação profunda 
    e expansão de resultados por scrolling iterativo.
    """
    print(f"\n[DRE] A iniciar recolha massiva de diplomas do Diário da República...")
    collected_links = set()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            page.goto("https://diariodarepublica.pt/dr/home", wait_until="load", timeout=30000)
            page.wait_for_timeout(4000)
            
            print("   -> A expandir o catálogo dinâmico via scroll sequencial...")
            for scroll_step in range(30): # 30 ciclos de scroll profundo para injetar milhares de links
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000)
                
                elements = page.query_selector_all('a[href*="/dr/detalhe/"]')
                for el in elements:
                    href = el.get_attribute("href")
                    if href:
                        full_url = urljoin("https://diariodarepublica.pt", href)
                        collected_links.add(full_url)
                        
                if len(collected_links) >= target_count:
                    break
                    
            print(f"   -> Capturados {len(collected_links)} diplomas do DRE.")

        except Exception as e:
            print(f"   [ERRO DRE]: {e}")
        finally:
            browser.close()
            
    return [{"url": link, "type": "DRE"} for link in collected_links]


def save_dataset(data, filename="dataset_spiderthrone_mass.csv"):
    core_docs = [
        {"url": "https://diariodarepublica.pt/dr/detalhe/decreto-lei/269-1998-566629", "type": "DRE"},
        {"url": "https://diariodarepublica.pt/dr/detalhe/lei/144-2015-7021319", "type": "DRE"}
    ]
    
    final_data = []
    seen = set()
    for doc in core_docs + data:
        if doc['url'] not in seen:
            final_data.append(doc)
            seen.add(doc['url'])

    print(f"\nA gravar um total de {len(final_data)} registos no ficheiro '{filename}'...")
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["url", "type"])
        writer.writeheader()
        writer.writerows(final_data)
    print("Processo concluído com sucesso!")


if __name__ == "__main__":
    print("=== SPIDERTHRONE MASS HARVESTER (PRODUÇÃO) ===")
    dgsi_links = harvest_dgsi_mass_engine(target_count=1000)
    dre_links = harvest_dre_mass_engine(target_count=300)
    
    save_dataset(dgsi_links + dre_links)