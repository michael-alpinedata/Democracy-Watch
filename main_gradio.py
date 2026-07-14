# main_gradio.py
import gradio as gr
import pandas as pd
import numpy as np
import re
from collections import Counter

# On importe ton Embedder ONNX tout propre
from src.embed.embedder import Embedder

# ==========================================
# 1. PRÉPARATION DU JEU DE DONNÉES DE TEST
# ==========================================
demo_data = [
    {
        "id": "AMD_01",
        "auteur": "Groupe A",
        "exposeSommaire": "Cet amendement du groupe A vise à soumettre les investissements étrangers dans une société sportive à l’autorisation préalable du ministre chargé de l’économie, dans les conditions déjà prévues à l’article L. 151‑3 du code monétaire et financier, comme l’a souligné le rapport d’information sénatorial sur l’intervention des fonds d’investissement dans le football professionnel français."
    },
    {
        "id": "AMD_02",
        "auteur": "Groupe B",
        "exposeSommaire": "Le présent amendement a pour but d'encadrer les investissements étrangers dans le sport professionnel. Il convient de soumettre ces flux à l'autorisation préalable du ministre de l'économie, selon le mécanisme de l'article L. 151-3 du code monétaire et financier, afin de protéger nos clubs des fonds d'investissement."
    },
    {
        "id": "AMD_03",
        "auteur": "Groupe C",
        "exposeSommaire": "Cet amendement vise à soutenir le développement du sport amateur en augmentant les subventions allouées aux petits clubs de football et de rugby dans les zones rurales."
    },
    {
        "id": "AMD_04",
        "auteur": "Groupe D",
        "exposeSommaire": "Afin de protéger la souveraineté sportive nationale, cet amendement propose de soumettre à l'autorisation préalable du ministre de l'Économie tout investissement étranger dans les sociétés sportives françaises (mécanisme similaire à l'article L. 151-3 du code monétaire et financier)."
    }
]

df = pd.DataFrame(demo_data)

# ==========================================
# 2. NETTOYAGE ET PRÉ-TRAITEMENT
# ==========================================
FRENCH_STOP_WORDS = {
    "le", "la", "les", "de", "du", "des", "un", "une", "et", "en", "que", "qui", 
    "pour", "dans", "par", "sur", "avec", "est", "sont", "au", "aux", "ce", "ces", 
    "cette", "cet", "a", "visé", "visant", "amendement", "groupe", "présent", "vise",
    "propose", "permet", "afin", "loi", "article", "alinéa"
}

def clean_text(text):
    """Nettoie le texte en retirant les formules introductives classiques."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"cet amendement (du groupe [\w\s]+ )?vise à\s+", "", text)
    text = re.sub(r"le présent amendement (propose|a pour but)\s+", "", text)
    text = re.sub(r"[^\w\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

df['clean_es'] = df['exposeSommaire'].apply(clean_text)

# ==========================================
# 3. MOTEUR VECTORIEL & SIMILARITÉ (ONNX)
# ==========================================
encoder = Embedder()

# Encodage préalable du corpus
corpus_embeddings = encoder.encode_batch(df['clean_es'].tolist(), normalize=True)

def find_similar_amendments(query_text, top_n=3):
    """Trouve les amendements les plus similaires sémantiquement."""
    cleaned_query = clean_text(query_text)
    query_embedding = encoder.encode(cleaned_query, normalize=True)
    
    # Produit scalaire NumPy direct (vecteurs L2-normalisés)
    cos_scores = np.dot(corpus_embeddings, query_embedding)
    
    # Tri des résultats décroissants
    top_results = np.argsort(-cos_scores)[:top_n]
    
    results = []
    for idx in top_results:
        idx = int(idx)
        score = float(cos_scores[idx])
        results.append({
            "ID": df.iloc[idx]['id'],
            "Auteur": df.iloc[idx]['auteur'],
            "Score de similarité": f"{score:.2%}",
            "Exposé Sommaire": df.iloc[idx]['exposeSommaire']
        })
    return pd.DataFrame(results)

# ==========================================
# 4. ANALYSE FRÉQUENTIELLE (PUR PYTHON)
# ==========================================
def extract_top_ngrams(n=2, top_k=10):
    """Extrait les n-grammes les plus fréquents de tout le corpus en pur Python."""
    all_ngrams = []
    
    for text in df['clean_es']:
        # On découpe en mots en éliminant les stop words et les mots trop courts
        words = [w for w in text.split() if w not in FRENCH_STOP_WORDS and len(w) >= 3]
        
        # Génération des n-grammes glissants
        if len(words) >= n:
            for i in range(len(words) - n + 1):
                ngram = " ".join(words[i:i+n])
                all_ngrams.append(ngram)
                
    # Comptage des occurrences
    counts = Counter(all_ngrams)
    most_common = counts.most_common(top_k)
    
    if not most_common:
        return pd.DataFrame(columns=['N-gram', 'Nombre d\'occurrences'])
        
    return pd.DataFrame(most_common, columns=['N-gram', 'Nombre d\'occurrences'])

# ==========================================
# 5. CONFIGURATION DE L'INTERFACE GRADIO
# ==========================================
with gr.Blocks(title="D4G - Analyse Sémantique des Amendements", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🏛️ Détecteur d'Amendements Similaires & Analyse Thématique")
    gr.Markdown(
        "Ce prototype permet de détecter les amendements 'copiés-collés' (kits de lobbying) "
        "grâce à la similarité sémantique et d'analyser les termes récurrents utilisés."
    )
    
    with gr.Tab("🔍 Recherche par Similarité"):
        gr.Markdown("### Collez un exposé sommaire pour trouver les amendements du corpus qui s'en rapprochent le plus.")
        
        with gr.Row():
            with gr.Column(scale=2):
                input_text = gr.Textbox(
                    label="Exposé sommaire à tester", 
                    placeholder="Saisissez ici le texte de l'exposé sommaire d'un amendement...",
                    lines=8,
                    value=demo_data[0]["exposeSommaire"]
                )
                btn_search = gr.Button("Analyser la similarity", variant="primary")
            
            with gr.Column(scale=3):
                output_table = gr.Dataframe(
                    headers=["ID", "Auteur", "Score de similarité", "Exposé Sommaire"],
                    label="Amendements les plus proches trouvés"
                )
        
        btn_search.click(
            fn=find_similar_amendments, 
            inputs=[input_text], 
            outputs=[output_table]
        )
        
    with gr.Tab("📊 Analyse des Mots-Clés (Lobbying)"):
        gr.Markdown("### Extraction des expressions répétées (N-Grammes) qui révèlent des éléments de langage partagés.")
        
        with gr.Row():
            with gr.Column():
                ngram_selector = gr.Slider(
                    minimum=1, maximum=3, step=1, value=2, 
                    label="Nombre de mots par expression (N-gramme)"
                )
                btn_analyse = gr.Button("Lancer l'analyse fréquentielle", variant="primary")
            
            with gr.Column():
                freq_table = gr.Dataframe(
                    headers=["N-gram", "Nombre d'occurrences"],
                    label="Expressions clés les plus caractéristiques"
                )
        
        btn_analyse.click(
            fn=extract_top_ngrams, 
            inputs=[ngram_selector], 
            outputs=[freq_table]
        )

if __name__ == "__main__":
    demo.launch()