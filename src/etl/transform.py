from src.embed.embedder import Embedder

def transform_amendements(data: list[dict]) -> list[dict]:
    """
    Enrichit les données extraites en mémoire avec les embeddings générés par ONNX.
    """
    # Initialisation de l'embedder (modèle + tokenizer)
    embedder = Embedder()
    
    # Préparation des textes (ajuste les clés selon ton JSON)
    textes_a_vectoriser = [
        (str(item.get("dispositif", "")) + " " + str(item.get("exposeSommaire", ""))).strip() 
        for item in data
    ]
        
    # Calcul par lot (très rapide)
    embeddings_matrix = embedder.encode_batch(textes_a_vectoriser)
    
    # Injection des vecteurs dans les dictionnaires existants
    for i, item in enumerate(data):
        if textes_a_vectoriser[i]:
            item['embedding'] = embeddings_matrix[i].tolist()
        else:
            item['embedding'] = None
            
    return data