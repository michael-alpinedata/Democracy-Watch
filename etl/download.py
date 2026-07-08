import json
import os
from time import sleep

import httpx

LEGISLATURE = 17
# Liste des apis à télécharger
APIS = ["dossiers", "documents", "amendements"]

API_READ_TIMEOUT = 30 

START_PAGE = 1
MAX_PAGE = 1000
BATCH_SIZE = 500
BASE_URL = "https://parlement.tricoteuses.fr/"


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
        except httpx.HTTPStatusError as e:
            # Si le serveur dit "Trop de requêtes" (429), on attend plus longtemps
            if e.response.status_code == 429:
                print(f"Rate limited. Attente de {wait_time}s...")
                time.sleep(wait_time)
                wait_time *= 2 # On double le temps d'attente
            else:
                raise e # Erreur fatale (ex: 404), on arrête
        except Exception as e:
            print(f"Erreur de connexion (tentative {attempt+1}): {e}")
            time.sleep(wait_time)
            wait_time *= 2
            
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

def run_download():
    for api in APIS:
        print("Fetching ", api)
        # On peut définir dynamiquement le point de départ
        # Par exemple : on commence là où le fichier le plus récent s'est arrêté
        # Ici, on garde START_PAGE pour la simplicité, ou on peut calculer le max
        for page, data in get_api_data(api, START_PAGE):
            save(data, api, page)
            sleep(0.3)

if __name__ == "__main__":
    run_download()
