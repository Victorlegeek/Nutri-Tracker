# utils/ia_enrichissement.py
# Enrichissement automatique IA via Groq API (gratuite)
# Inscription gratuite : https://console.groq.com
# Cle API : https://console.groq.com/keys

import json
import os
import sys
import threading
import urllib.request
import urllib.error
import difflib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(BASE_DIR, 'data')
CFG_FILE  = os.path.join(BASE_DIR, 'config.json')

GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"   # modele gratuit le plus puissant

# Nombre minimum d'ajouts voulus par session
ALIMENTS_PAR_SESSION    = 8
SUPPLEMENTS_PAR_SESSION = 3


# ─── CONFIG (cle API) ─────────────────────────────────────────────────────────

def lire_config() -> dict:
    try:
        with open(CFG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def sauvegarder_config(cfg: dict):
    with open(CFG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def lire_cle_api() -> str:
    return lire_config().get('groq_api_key', '').strip()

def sauvegarder_cle_api(cle: str):
    cfg = lire_config()
    cfg['groq_api_key'] = cle.strip()
    sauvegarder_config(cfg)


# ─── APPEL GROQ ───────────────────────────────────────────────────────────────

def appel_groq(prompt_systeme: str, prompt_user: str, cle: str,
               max_tokens: int = 2000) -> str:
    """Appelle Groq API et retourne le texte de la reponse."""
    payload = json.dumps({
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": prompt_systeme},
            {"role": "user",   "content": prompt_user},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.4,
    }).encode('utf-8')

    req = urllib.request.Request(
        GROQ_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cle}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data["choices"][0]["message"]["content"]


# ─── UTILITAIRES JSON ────────────────────────────────────────────────────────

def charger_json(chemin: str) -> dict:
    try:
        with open(chemin, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def sauvegarder_json(chemin: str, data: dict):
    with open(chemin, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def noms_existants_aliments() -> list[str]:
    data = charger_json(os.path.join(DATA_DIR, 'aliments.json'))
    return [a['nom'].lower().strip() for a in data.get('aliments', [])]

def noms_existants_supplements() -> list[str]:
    data = charger_json(os.path.join(DATA_DIR, 'supplements.json'))
    return [s['nom'].lower().strip() for s in data.get('supplements', [])]

def est_doublon(nom: str, noms_existants: list[str], seuil=0.85) -> bool:
    nom = nom.lower().strip()
    if nom in noms_existants:
        return True
    for existant in noms_existants:
        ratio = difflib.SequenceMatcher(None, nom, existant).ratio()
        if ratio >= seuil:
            return True
    return False

def nettoyer_json_ia(texte: str) -> str:
    """Extrait le JSON brut depuis la reponse IA (enleve markdown etc.)"""
    texte = texte.strip()
    # Enlever ```json ... ```
    if '```' in texte:
        start = texte.find('```')
        end   = texte.rfind('```')
        if start != end:
            texte = texte[start+3:end]
            if texte.startswith('json'):
                texte = texte[4:]
    texte = texte.strip()
    return texte


# ─── GENERATION ALIMENTS ─────────────────────────────────────────────────────

PROMPT_SYS_ALIMENTS = """Tu es un expert en nutrition. Tu generes des donnees nutritionnelles
precises pour une application de suivi alimentaire.
Reponds UNIQUEMENT avec du JSON valide, aucun texte autour, aucun markdown.
Les valeurs doivent etre pour 100g/100ml, realistes et verifiees."""

def prompt_aliments(noms_existants: list[str], n: int) -> str:
    exemples_existants = ', '.join(noms_existants[:15])
    categories = [
        "viandes", "poissons", "oeufs", "feculents", "legumes",
        "fruits", "laitiers", "oleagineux", "legumineuses",
        "boissons", "sucres", "matieres_grasses", "charcuterie"
    ]
    return f"""
Genere exactement {n} aliments nutritionnels qui n'existent PAS dans cette liste :
{exemples_existants}

Choisis des aliments varies, utiles pour le sport et la sante.
Priorite : aliments que les sportifs mangent souvent (proteines, feculents complexes, legumes).

Reponds avec ce JSON exact (tableau d'aliments) :
[
  {{
    "id": "identifiant_court_sans_espaces",
    "nom": "Nom complet de l'aliment",
    "marque": "Standard",
    "categorie": "une de : {', '.join(categories)}",
    "favoris": false,
    "valeurs_100g": {{
      "calories": 120,
      "proteines": 23.0,
      "glucides": 0.0,
      "sucres": 0.0,
      "lipides": 2.5,
      "acides_gras_satures": 0.7,
      "fibres": 0.0,
      "sel": 0.1
    }}
  }}
]
"""

def ajouter_aliments_ia(nouveaux: list, callback=None) -> int:
    """Ajoute les aliments generes par l'IA au fichier JSON. Retourne le nb ajoutes."""
    chemin = os.path.join(DATA_DIR, 'aliments.json')
    data   = charger_json(chemin)
    if 'aliments' not in data:
        data['aliments'] = []

    noms = noms_existants_aliments()
    ajoutes = 0

    for aliment in nouveaux:
        nom = aliment.get('nom', '').strip()
        if not nom:
            continue
        if est_doublon(nom, noms):
            continue
        # Validation minimale des champs
        v = aliment.get('valeurs_100g', {})
        champs_requis = ['calories', 'proteines', 'glucides', 'lipides']
        if not all(k in v for k in champs_requis):
            continue
        # Securite : forcer les valeurs manquantes
        for champ in ['sucres', 'acides_gras_satures', 'fibres', 'sel']:
            v.setdefault(champ, 0.0)
        # Forcer id unique si absent
        if not aliment.get('id'):
            import uuid
            aliment['id'] = str(uuid.uuid4())[:8]
        aliment['valeurs_100g'] = v
        aliment.setdefault('marque', 'Standard')
        aliment.setdefault('categorie', 'autre')
        aliment.setdefault('favoris', False)

        data['aliments'].append(aliment)
        noms.append(nom.lower())
        ajoutes += 1
        if callback:
            callback(f"+ Aliment : {nom}")

    sauvegarder_json(chemin, data)
    return ajoutes


# ─── GENERATION SUPPLEMENTS ──────────────────────────────────────────────────

PROMPT_SYS_SUPPS = """Tu es un expert en nutrition sportive et complements alimentaires.
Tu generes des donnees precises sur les complements alimentaires.
Reponds UNIQUEMENT avec du JSON valide, aucun texte autour."""

def prompt_supplements(noms_existants: list[str], n: int) -> str:
    types_valides = ['Proteine', 'Creatine', 'Vitamine', 'Mineral',
                     'Acides gras', 'Pre-workout', 'Gainer', 'BCAA', 'Autre']
    return f"""
Genere exactement {n} complements alimentaires qui n'existent PAS dans cette liste :
{', '.join(noms_existants)}

Choisis des complements utiles et populaires pour les sportifs.

Reponds avec ce JSON exact :
[
  {{
    "id": "identifiant_court",
    "nom": "Nom du complement",
    "type": "un de : {', '.join(types_valides)}",
    "dose_habituelle": 30,
    "kcal_dose": 120,
    "prot_dose": 24.0,
    "gluc_dose": 3.0,
    "lip_dose": 1.5,
    "marque": "Standard",
    "note": "Conseil d'utilisation court"
  }}
]
"""

def ajouter_supplements_ia(nouveaux: list, callback=None) -> int:
    """Ajoute les supplements generes au fichier JSON."""
    chemin = os.path.join(DATA_DIR, 'supplements.json')
    data   = charger_json(chemin)
    if 'supplements' not in data:
        data['supplements'] = []
    if 'prises' not in data:
        data['prises'] = {}

    noms   = noms_existants_supplements()
    ajoutes = 0

    for supp in nouveaux:
        nom = supp.get('nom', '').strip()
        if not nom:
            continue
        if est_doublon(nom, noms):
            continue
        import uuid
        supp.setdefault('id', str(uuid.uuid4())[:8])
        supp.setdefault('dose_habituelle', 30)
        supp.setdefault('kcal_dose', 0)
        supp.setdefault('prot_dose', 0)
        supp.setdefault('gluc_dose', 0)
        supp.setdefault('lip_dose',  0)
        supp.setdefault('marque', 'Standard')
        supp.setdefault('note', '')
        supp.setdefault('type', 'Autre')

        data['supplements'].append(supp)
        noms.append(nom.lower())
        ajoutes += 1
        if callback:
            callback(f"+ Supplement : {nom}")

    sauvegarder_json(chemin, data)
    return ajoutes


# ─── ORCHESTRATEUR PRINCIPAL ──────────────────────────────────────────────────

def enrichir_base(cle_api: str, callback=None, n_aliments=ALIMENTS_PAR_SESSION,
                  n_supps=SUPPLEMENTS_PAR_SESSION):
    """
    Fonction principale appellee au demarrage.
    callback(message: str) pour afficher la progression dans l'UI.
    """
    if not cle_api:
        if callback:
            callback("IA : aucune cle API configuree — ignoree")
        return

    def log(msg):
        print(f"[IA] {msg}")
        if callback:
            callback(msg)

    # ── Aliments ──────────────────────────────────────────────────────────────
    try:
        log("Recherche de nouveaux aliments...")
        noms = noms_existants_aliments()
        prompt = prompt_aliments(noms, n_aliments)
        reponse = appel_groq(PROMPT_SYS_ALIMENTS, prompt, cle_api, max_tokens=2500)
        texte_json = nettoyer_json_ia(reponse)
        nouveaux_aliments = json.loads(texte_json)
        if not isinstance(nouveaux_aliments, list):
            raise ValueError("Format inattendu (pas une liste)")
        nb = ajouter_aliments_ia(nouveaux_aliments, callback=log)
        log(f"✓ {nb} aliment(s) ajoute(s) a la base")
    except urllib.error.HTTPError as e:
        log(f"Erreur API Groq ({e.code}) : verifie ta cle API")
    except json.JSONDecodeError as e:
        log(f"Erreur parsing JSON aliments : {e}")
    except Exception as e:
        log(f"Erreur aliments : {e}")

    # ── Supplements ───────────────────────────────────────────────────────────
    try:
        log("Recherche de nouveaux supplements...")
        noms_s = noms_existants_supplements()
        prompt_s = prompt_supplements(noms_s, n_supps)
        reponse_s = appel_groq(PROMPT_SYS_SUPPS, prompt_s, cle_api, max_tokens=1000)
        texte_json_s = nettoyer_json_ia(reponse_s)
        nouveaux_supps = json.loads(texte_json_s)
        if not isinstance(nouveaux_supps, list):
            raise ValueError("Format inattendu")
        nb_s = ajouter_supplements_ia(nouveaux_supps, callback=log)
        log(f"✓ {nb_s} supplement(s) ajoute(s)")
    except urllib.error.HTTPError as e:
        log(f"Erreur API Groq ({e.code}) : verifie ta cle API")
    except json.JSONDecodeError as e:
        log(f"Erreur parsing JSON supplements : {e}")
    except Exception as e:
        log(f"Erreur supplements : {e}")

    log("Enrichissement IA termine !")


def enrichir_en_arriere_plan(callback=None):
    """Lance l'enrichissement dans un thread pour ne pas bloquer l'UI."""
    cle = lire_cle_api()
    t = threading.Thread(
        target=enrichir_base,
        args=(cle, callback),
        daemon=True,
    )
    t.start()
    return t
