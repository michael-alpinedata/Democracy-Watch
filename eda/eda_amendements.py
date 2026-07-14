import marimo

__generated_with = "0.23.9"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import json
    import pandas as pd
    import os
    from pathlib import Path
    import matplotlib.pyplot as plt

    return Path, json, mo, pd, plt


@app.cell
def _(mo):
    mo.md("""
    # EDA : Analyse des Amendements (Tricoteuses)
    Ce notebook explore la structure des données JSON pour identifier le payload textuel des amendements et dimensionner notre stratégie de chunking pour le système RAG.
    """)
    return


@app.cell
def _(Path, mo):
    # Configuration des chemins d'accès aux données
    DATA_DIR = Path("../data/raw")
    AMENDEMENTS_JSON_PATH = DATA_DIR / "amendements.json"

    file_exists = AMENDEMENTS_JSON_PATH.exists()

    if not file_exists:
        status = mo.md(f"⚠️ **Attention :** Le fichier `{AMENDEMENTS_JSON_PATH}` est introuvable. Pensez à exécuter `just download` ou `uv run main.py -d` au préalable.")
    else:
        status = mo.md(f"✅ Fichier trouvé : `{AMENDEMENTS_JSON_PATH}`")

    status
    return AMENDEMENTS_JSON_PATH, file_exists


@app.cell
def _(AMENDEMENTS_JSON_PATH, file_exists, json):
    # Chargement d'un échantillon ou de la totalité du fichier JSON
    amendements_data = []
    if file_exists:
        with open(AMENDEMENTS_JSON_PATH, "r", encoding="utf-8") as f:
            amendements_data = json.load(f)

    total_records = len(amendements_data)
    return amendements_data, total_records


@app.cell
def _(mo, total_records):
    mo.md(f"**Nombre total d'amendements chargés :** {total_records}")
    return


@app.cell
def _(amendements_data, mo):
    # Inspection de la structure globale du premier élément
    if amendements_data:
        sample_entry = amendements_data[0]
        structure_preview = mo.vstack([
            mo.md("### Structure racine d'un amendement :"),
            mo.plain_text(str(list(sample_entry.keys()))),
            mo.md("### Aperçu brut du premier élément :"),
            mo.tree(sample_entry)  # Permet d'explorer l'arborescence de manière interactive
        ])
    else:
        structure_preview = mo.md("Aucune donnée disponible pour l'inspection.")
        sample_entry = {}

    structure_preview
    return


@app.cell
def _(amendements_data, mo, pd):
    # Extraction et identification du payload textuel
    # À ajuster selon la clé exacte trouvée (ex: 'corps', 'texte', 'dispositif', etc.)
    records = []

    for entry in amendements_data:

        uid = entry.get("uid")
        exposeSommaire = entry.get("exposeSommaire", "")
        dispositif = entry.get("dispositif", "")

        records.append({
            "uid": uid,
            "expose_sommaire": exposeSommaire,
            "expose_sommaire_char_length": len(exposeSommaire) if exposeSommaire else 0,
            "expose_sommaire_word_count": len(exposeSommaire.split()) if exposeSommaire else 0,
            "dispositif": dispositif,
            "dispositif_char_length": len(dispositif) if dispositif else 0,
            "dispositif_word_count": len(dispositif.split()) if dispositif else 0,
        })

    df = pd.DataFrame(records)
    mo.md("### DataFrame des payloads textuels extrait")
    return (df,)


@app.cell
def _(df, mo):
    # Aperçu du tableau extrait
    aperçu_table = mo.vstack([
        mo.md("#### Premières lignes extraites :"),
        mo.ui.table(df.head(10))  # Rendu propre et interactif du DataFrame
    ])
    return (aperçu_table,)


@app.cell
def _(aperçu_table, df, mo):
    # Statistiques descriptives pour le chunking
    stats = df[["expose_sommaire_char_length", "expose_sommaire_word_count", "dispositif_char_length", "dispositif_word_count"]].describe()

    stats_view = mo.vstack([
        mo.md("### Statistiques de distribution des longueurs de texte"),
        mo.md("Ces métriques permettent de dimensionner la taille de vos fenêtres (*chunk_size*) et le chevauchement (*chunk_overlap*)."),
        mo.ui.table(stats)  # Rend les statistiques lisibles sous forme de tableau
    ])

    # Pour afficher les deux blocs verticalement dans votre notebook :
    mo.vstack([
        aperçu_table,
        stats_view
    ])
    return


@app.cell
def _(df, plt):
    # Visualisation de la distribution
    fig1, ax1 = plt.subplots(1, 2, figsize=(12, 5))

    ax1[0].hist(df["expose_sommaire_char_length"], bins=50, color="skyblue", edgecolor="black")
    ax1[0].set_title("Distribution de la longueur (Caractères)")
    ax1[0].set_xlabel("Nombre de caractères")
    ax1[0].set_ylabel("Fréquence")

    ax1[1].hist(df["expose_sommaire_word_count"], bins=50, color="salmon", edgecolor="black")
    ax1[1].set_title("Distribution du nombre de mots")
    ax1[1].set_xlabel("Nombre de mots")
    ax1[1].set_ylabel("Fréquence")

    plt.tight_layout()
    fig1
    return


@app.cell
def _(df, plt):
    # Visualisation de la distribution
    fig2, ax2 = plt.subplots(1, 2, figsize=(12, 5))

    ax2[0].hist(df["dispositif_char_length"], bins=50, color="skyblue", edgecolor="black")
    ax2[0].set_title("Distribution de la longueur (Caractères)")
    ax2[0].set_xlabel("Nombre de caractères")
    ax2[0].set_ylabel("Fréquence")

    ax2[1].hist(df["dispositif_word_count"], bins=50, color="salmon", edgecolor="black")
    ax2[1].set_title("Distribution du nombre de mots")
    ax2[1].set_xlabel("Nombre de mots")
    ax2[1].set_ylabel("Fréquence")

    plt.tight_layout()
    fig2
    return


if __name__ == "__main__":
    app.run()
