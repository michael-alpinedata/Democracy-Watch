import json
import os
from time import sleep

import httpx
import logging

LEGISLATURE = 17
# Liste des apis à télécharger
APIS = ["dossiers", "documents", "amendements"]

API_READ_TIMEOUT = 30 

# On peut définir dynamiquement le point de départ
# Par exemple : on commence là où le fichier le plus récent s'est arrêté
START_PAGE = 1
MAX_PAGE = 1000
BATCH_SIZE = 500
BASE_URL = "https://parlement.tricoteuses.fr/"

# Configuration basique du log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def save(data, api, page):
    # Modification : Sauvegarde par page pour éviter les doublons et les réécritures en cas de timeout pendant le DL
    os.makedirs(f"./data/{api}", exist_ok=True)
    with open(f"./data/{api}/page_{page}.json", "w") as f:
        json.dump(data, f)


import time

def get(page, base_url):
    params = f"?page={page}&perPage={BATCH_SIZE}&legislature={LEGISLATURE}"
    url = base_url + params
    
    # Stratégie de "Exponential Backoff" : on attend de plus en plus longtemps
    wait_time = 2 
    for attempt in range(5): # On essaie 5 fois avant d'abandonner
        try:
            response = httpx.get(url, timeout=API_READ_TIMEOUT)
            response.raise_for_status()
            return response
        except Exception as e:
            # On logue l'erreur avec le niveau WARNING
            logging.warning(f"Tentative {attempt+1} échouée pour page {page}: {e}")
            time.sleep(wait_time)
            wait_time *= 2 
            
    logging.error(f"Abandon après 5 tentatives pour la page {page}")
    return None

def get_api_data(api, start_page): # Ajout du paramètre start_page
    base_url = BASE_URL + api + "/json"
    for page in range(start_page, MAX_PAGE):
        # On vérifie sur le disque avant de lancer la requête
        if os.path.exists(f"./data/{api}/page_{page}.json"):
            print(f"\tpage {page} déjà présente, saut...")
            continue
            
        print("\tpage: ", page)
        response = get(page, base_url)
        if response is None:
            break

        current_batch_data = response.json()
        if len(current_batch_data["data"]) == 0:
            break
        
        yield page, current_batch_data["data"]

def merge_pages_to_json(api):
    print(f"Fusion des pages pour : {api}...")
    folder_path = f"./data/{api}"
    merged_data = {} # Dictionnaire indexé par UID pour le dédoublonnage

    # On liste tous les fichiers de page
    files = [f for f in os.listdir(folder_path) if f.startswith("page_") and f.endswith(".json")]
    
    # Tri pour fusionner dans l'ordre (facultatif mais plus propre)
    files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))

    for filename in files:
        with open(os.path.join(folder_path, filename), "r") as f:
            try:
                page_data = json.load(f)
                # On ajoute chaque élément dans le dictionnaire
                for item in page_data:
                    merged_data[item["uid"]] = item
            except json.JSONDecodeError:
                print(f"Erreur de lecture sur {filename}")

    # Sauvegarde du fichier final consolidé
    with open(f"./data/{api}.json", "w") as f:
        # On repasse en liste pour que le fichier final soit une liste d'objets
        json.dump(list(merged_data.values()), f, ensure_ascii=False, indent=2)
    
    print(f"Fusion terminée ! {len(merged_data)} {api} uniques enregistrés.")

def run_download():
    for api in APIS:
        logging.info(f"Début du fetch pour : {api}")
        for page, data in get_api_data(api, START_PAGE):
            save(data, api, page)
            # Passage de 0.3 à 2.0 secondes pour être plus respectueux
            sleep(2.0)

        # Une fois le téléchargement terminé :
        merge_pages_to_json(api)

if __name__ == "__main__":
    run_download()
