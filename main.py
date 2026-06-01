# main.py - Point d'entrée de NutriTracker
# Lancer avec : python main.py depuis C:/NutriTracker/
import sys
import os

# S'assurer que le dossier du projet est dans le path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Vérification des dépendances avant lancement
def verifier_dependances():
    manquantes = []
    try:
        import tkinter
    except ImportError:
        manquantes.append("tkinter (inclus avec Python normalement)")
    try:
        import json, os, shutil, uuid, difflib, datetime
    except ImportError as e:
        manquantes.append(str(e))

    if manquantes:
        print("✗ Dépendances manquantes :")
        for m in manquantes:
            print(f"  - {m}")
        print("\nRelance install_nutri.bat en administrateur.")
        sys.exit(1)

    # Bibliothèques optionnelles (avertissement seulement)
    optionnelles = {
        'ttkbootstrap': 'thème moderne (pip install ttkbootstrap)',
        'requests':     'recherche web (pip install requests)',
        'bs4':          'scraping nutritionnel (pip install beautifulsoup4)',
        'cv2':          'OCR images (pip install opencv-python)',
        'pytesseract':  'scan étiquettes (pip install pytesseract)',
        'PIL':          'traitement images (pip install Pillow)',
    }
    for mod, info in optionnelles.items():
        try:
            __import__(mod)
        except ImportError:
            print(f"  ⚠ Module optionnel absent : {mod} — {info}")

def main():
    verifier_dependances()

    # Créer les fichiers de données s'ils n'existent pas
    _initialiser_donnees()

    # Lancer l'interface
    from ui.main_window import NutriApp
    app = NutriApp()
    app.mainloop()

def _initialiser_donnees():
    """Crée les fichiers JSON vides si absents"""
    import json
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)

    fichiers_defaut = {
        'journal.json':     {"version": "1.0", "journal": {}},
        'supplements.json': {"version": "1.0", "supplements": []},
        'objectifs.json': {
            "version": "1.0",
            "profil": {
                "nom": "", "age": 25, "taille_cm": 175,
                "poids_kg": 75, "sexe": "homme",
                "activite": "moderee", "objectif": "maintien"
            },
            "objectifs_journaliers": {
                "calories": 2000, "proteines": 150, "glucides": 200,
                "lipides": 65, "fibres": 25, "sel": 6, "sucres": 50
            }
        },
    }

    for nom_fichier, contenu_defaut in fichiers_defaut.items():
        chemin = os.path.join(data_dir, nom_fichier)
        if not os.path.exists(chemin):
            with open(chemin, 'w', encoding='utf-8') as f:
                json.dump(contenu_defaut, f, ensure_ascii=False, indent=2)
            print(f"  ✓ Créé : data/{nom_fichier}")

    # aliments.json est fourni avec le projet — avertissement si absent
    if not os.path.exists(os.path.join(data_dir, 'aliments.json')):
        print("  ⚠ data/aliments.json manquant — base de données vide")
        with open(os.path.join(data_dir, 'aliments.json'), 'w', encoding='utf-8') as f:
            json.dump({"version": "1.0", "aliments": []}, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
