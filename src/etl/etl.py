from src.database import get_tables_definition
from src.etl.extraction import extract
from src.etl.loading import load
from src.etl.transform import transform_amendements

def _get_table_metadata(table):
    tablename = table.name
    # On exclut 'embedding' des champs à chercher dans le JSON
    fields = [field.name for field in table.columns if field.name != 'embedding']
    return tablename, fields

def run_etl():
    """
    Extract from JSON files in './data/raw', transform if needed, and persist data.
    """
    tables = get_tables_definition()
    for table in tables:
        tablename, fields = _get_table_metadata(table)
        
        # 1. EXTRACT : Chargement en mémoire depuis le JSON
        data = extract(tablename, fields)
        
        # 2. TRANSFORM : Interception ciblée (Design Pattern : Strategy / Router)
        if tablename == "amendements" and data:
            print(f"Transformation en cours pour la table : {tablename}...")
            data = transform_amendements(data)
            
        # 3. LOAD : Insertion en base de données
        if data:
            load(table, data)