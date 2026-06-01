# ui/sante.py
# Suivi santé complet : poids, IMC, masse grasse (US Navy), tour de taille,
# hydratation, sommeil, fréquence cardiaque, forme subjective, VO2max estimé

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta
import json, os, sys, math

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

SANTE_FILE = os.path.join(BASE_DIR, 'data', 'sante.json')

C = {
    'bg':         '#0e0e12',
    'surface':    '#16161d',
    'surface2':   '#1e1e27',
    'surface3':   '#26262f',
    'border':     '#252530',
    'text':       '#f0f0f5',
    'text_muted': '#6b7280',
    'accent':     '#7c6aff',
    'accent_dim': '#3d3580',
    'success':    '#22c55e',
    'warning':    '#f59e0b',
    'danger':     '#ef4444',
    'info':       '#38bdf8',
    'cal':        '#ff6b81',
    'prot':       '#4ade80',
    'grid':       '#1e1e2e',
}

FONT_SMALL  = ('Segoe UI', 8)
FONT_LABEL  = ('Segoe UI', 9)
FONT_BODY   = ('Segoe UI', 10)
FONT_BOLD   = ('Segoe UI', 10, 'bold')
FONT_H2     = ('Segoe UI', 12, 'bold')
FONT_H3     = ('Segoe UI', 11, 'bold')
FONT_TITLE  = ('Segoe UI Semibold', 14, 'bold')
FONT_NUM    = ('Segoe UI Semibold', 22, 'bold')
FONT_NUM_SM = ('Segoe UI Semibold', 15, 'bold')


# ─── STOCKAGE ─────────────────────────────────────────────────────────────────

def charger_sante() -> dict:
    try:
        with open(SANTE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'entrees': {}}

def sauvegarder_sante(data: dict):
    os.makedirs(os.path.dirname(SANTE_FILE), exist_ok=True)
    with open(SANTE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def sauvegarder_entree(entree: dict, jour: date = None):
    data = charger_sante()
    if 'entrees' not in data:
        data['entrees'] = {}
    key = (jour or date.today()).isoformat()
    data['entrees'][key] = entree
    sauvegarder_sante(data)

def charger_entrees_periode(nb_jours=30) -> list[tuple[date, dict]]:
    data = charger_sante()
    entrees = data.get('entrees', {})
    today = date.today()
    resultats = []
    for i in range(nb_jours):
        d = today - timedelta(days=i)
        key = d.isoformat()
        if key in entrees:
            resultats.append((d, entrees[key]))
    return list(reversed(resultats))

def charger_entree_jour(jour: date = None) -> dict:
    data = charger_sante()
    key = (jour or date.today()).isoformat()
    return data.get('entrees', {}).get(key, {})


# ─── CALCULS SANTÉ ────────────────────────────────────────────────────────────

def calcul_imc(poids_kg: float, taille_cm: float) -> float:
    if taille_cm <= 0:
        return 0
    return poids_kg / ((taille_cm / 100) ** 2)

def categorie_imc(imc: float) -> tuple[str, str]:
    """Retourne (catégorie, couleur)"""
    if imc < 16.5:  return ("Dénutrition sévère",  C['danger'])
    if imc < 18.5:  return ("Maigreur",             C['warning'])
    if imc < 25.0:  return ("Poids normal",         C['success'])
    if imc < 30.0:  return ("Surpoids",             C['warning'])
    if imc < 35.0:  return ("Obésité modérée",      C['danger'])
    if imc < 40.0:  return ("Obésité sévère",       C['danger'])
    return             ("Obésité morbide",           C['danger'])

def calcul_masse_grasse_navy(
        taille_cm: float, tour_cou_cm: float,
        tour_taille_cm: float, tour_hanches_cm: float = None,
        sexe: str = 'homme') -> float:
    """
    Formule US Navy (méthode des circonférences).
    Précision ±3% — valide pour adultes.
    """
    try:
        t = taille_cm
        if sexe == 'homme':
            mg = 86.010 * math.log10(tour_taille_cm - tour_cou_cm) \
               - 70.041 * math.log10(t) + 36.76
        else:
            if not tour_hanches_cm:
                return 0.0
            mg = 163.205 * math.log10(tour_taille_cm + tour_hanches_cm - tour_cou_cm) \
               - 97.684 * math.log10(t) - 78.387
        return max(0.0, round(mg, 1))
    except Exception:
        return 0.0

def calcul_masse_maigre(poids_kg: float, mg_pct: float) -> float:
    return round(poids_kg * (1 - mg_pct / 100), 1)

def categorie_masse_grasse(mg: float, sexe: str) -> tuple[str, str]:
    if sexe == 'homme':
        if mg < 6:   return ("Très faible (athlète)",  C['info'])
        if mg < 14:  return ("Athlète",                C['success'])
        if mg < 18:  return ("Fitness",                C['success'])
        if mg < 25:  return ("Normal",                 C['success'])
        if mg < 32:  return ("Au-dessus de la normale",C['warning'])
        return              ("Élevée",                 C['danger'])
    else:
        if mg < 14:  return ("Très faible",            C['info'])
        if mg < 21:  return ("Athlète",                C['success'])
        if mg < 25:  return ("Fitness",                C['success'])
        if mg < 32:  return ("Normal",                 C['success'])
        if mg < 39:  return ("Au-dessus de la normale",C['warning'])
        return              ("Élevée",                 C['danger'])

def calcul_vo2max_estime(fc_repos: int, age: int, sexe: str) -> float:
    """Estimation VO2max via formule de Uth-Sørensen (nécessite FC max estimée)."""
    fc_max = 220 - age
    if fc_repos <= 0:
        return 0
    vo2 = 15 * (fc_max / fc_repos)
    return round(vo2, 1)

def categorie_vo2max(vo2: float, age: int, sexe: str) -> tuple[str, str]:
    # Valeurs simplifiées pour homme 20-39 ans
    if vo2 < 35:  return ("Très faible",  C['danger'])
    if vo2 < 42:  return ("Faible",       C['warning'])
    if vo2 < 50:  return ("Moyen",        C['info'])
    if vo2 < 58:  return ("Bon",          C['success'])
    return              ("Excellent",     C['prot'])

def poids_ideal_devine(taille_cm: float, sexe: str) -> float:
    """Formule de Devine — poids idéal estimé."""
    taille_in = taille_cm / 2.54
    if sexe == 'homme':
        return round(50 + 2.3 * (taille_in - 60), 1)
    else:
        return round(45.5 + 2.3 * (taille_in - 60), 1)

def besoins_eau(poids_kg: float, activite: str = 'moderee') -> float:
    """Besoin en eau quotidien en litres."""
    base = poids_kg * 0.033
    bonus = {'sedentaire': 0, 'legere': 0.3, 'moderee': 0.5,
             'intense': 0.8, 'tres_intense': 1.2}.get(activite, 0.5)
    return round(base + bonus, 1)


# ═══════════════════════════════════════════════════════════════════════════════
# WIDGET GRAPHIQUE POIDS
# ═══════════════════════════════════════════════════════════════════════════════

class GraphiquePoids(tk.Canvas):
    """Courbe d'évolution du poids avec objectif et tendance."""
    PAD_L = 50; PAD_R = 20; PAD_T = 20; PAD_B = 40

    def __init__(self, parent, entrees, taille_cm, sexe, height=200, **kw):
        super().__init__(parent, bg=C['bg'], highlightthickness=0, height=height, **kw)
        self.entrees   = entrees
        self.taille_cm = taille_cm
        self.sexe      = sexe
        self.bind('<Configure>', lambda e: self._dessiner())

    def _dessiner(self):
        self.delete('all')
        W = self.winfo_width(); H = self.winfo_height()
        if W < 10 or H < 10: return

        pl, pr, pt, pb = self.PAD_L, self.PAD_R, self.PAD_T, self.PAD_B
        w_g = W - pl - pr; h_g = H - pt - pb

        data = [(d, e['poids']) for d, e in self.entrees
                if e.get('poids') and e['poids'] > 0]
        if not data:
            self.create_text(W//2, H//2, text="Pas encore de données de poids",
                             fill=C['text_muted'], font=FONT_LABEL)
            return

        poids_vals = [p for _, p in data]
        p_min = min(poids_vals) - 2
        p_max = max(poids_vals) + 2
        p_range = p_max - p_min or 1

        poids_ideal = poids_ideal_devine(self.taille_cm, self.sexe)

        # Grille
        for i in range(5):
            y = pt + (i / 4) * h_g
            v = p_max - (i / 4) * p_range
            self.create_line(pl, y, W-pr, y, fill=C['grid'], width=1)
            self.create_text(pl-4, y, text=f"{v:.1f}",
                             fill=C['text_muted'], font=FONT_SMALL, anchor='e')

        # Ligne poids idéal
        if p_min < poids_ideal < p_max:
            y_ideal = pt + h_g - ((poids_ideal - p_min) / p_range) * h_g
            self.create_line(pl, y_ideal, W-pr, y_ideal,
                             fill=C['success'], dash=(6, 4), width=1)
            self.create_text(W-pr-2, y_ideal-7,
                             text=f"Idéal {poids_ideal}kg",
                             fill=C['success'], font=FONT_SMALL, anchor='e')

        n = len(data)
        def _xy(idx):
            d, p = data[idx]
            x = pl + (idx / max(n-1,1)) * w_g
            y = pt + h_g - ((p - p_min) / p_range) * h_g
            return x, y

        # Courbe
        coords = []
        for i in range(n):
            x, y = _xy(i)
            coords.extend([x, y])
        if len(coords) >= 4:
            self.create_line(coords, fill=C['accent'], width=2,
                             smooth=True, capstyle='round')

        # Points
        mois_fr = ['Jan','Fev','Mar','Avr','Mai','Jun',
                   'Jul','Aou','Sep','Oct','Nov','Dec']
        for i in range(n):
            x, y = _xy(i)
            r = 4
            self.create_oval(x-r, y-r, x+r, y+r,
                             fill=C['bg'], outline=C['accent'], width=2)
            d, p = data[i]
            if i == n-1:
                self.create_text(x, y-12, text=f"{p:.1f}kg",
                                 fill=C['text'], font=FONT_SMALL)
            step = max(1, n//6)
            if i % step == 0 or i == n-1:
                self.create_text(x, H-pb+12,
                                 text=f"{d.day}/{mois_fr[d.month-1]}",
                                 fill=C['text_muted'], font=FONT_SMALL)

        # Tendance (régression linéaire simple)
        if n >= 3:
            xs = list(range(n))
            ys = [p for _, p in data]
            x_moy = sum(xs)/n; y_moy = sum(ys)/n
            num = sum((xs[i]-x_moy)*(ys[i]-y_moy) for i in range(n))
            den = sum((xs[i]-x_moy)**2 for i in range(n)) or 1
            a = num/den; b = y_moy - a*x_moy
            # Ligne tendance
            y0 = b; yn = a*(n-1)+b
            x0_px = pl
            xn_px = pl + w_g
            y0_px = pt + h_g - ((y0 - p_min)/p_range)*h_g
            yn_px = pt + h_g - ((yn - p_min)/p_range)*h_g
            self.create_line(x0_px, y0_px, xn_px, yn_px,
                             fill=C['warning'], dash=(3,6), width=1)
            delta = yn - y0
            sym = "↗" if delta > 0.1 else ("↘" if delta < -0.1 else "→")
            self.create_text(xn_px-2, yn_px-10,
                             text=f"{sym} {abs(delta):.1f}kg",
                             fill=C['warning'], font=FONT_SMALL, anchor='e')


# ═══════════════════════════════════════════════════════════════════════════════
# FORMULAIRE SAISIE QUOTIDIENNE
# ═══════════════════════════════════════════════════════════════════════════════

class DialogSaisiesSante(tk.Toplevel):
    """Dialogue de saisie des mesures du jour."""

    def __init__(self, parent, profil: dict, entree_existante: dict = None):
        super().__init__(parent)
        self.title("Mesures du jour")
        self.configure(bg=C['bg'])
        self.geometry("520x680")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.resultat = None
        self.profil   = profil
        self.entree   = entree_existante or {}
        self._construire()

    def _construire(self):
        tk.Label(self, text=f"Mesures du {date.today().strftime('%d/%m/%Y')}",
                 bg=C['bg'], fg=C['text'], font=FONT_TITLE).pack(pady=14, padx=20, anchor='w')

        # ScrollFrame interne
        canvas = tk.Canvas(self, bg=C['bg'], highlightthickness=0)
        sb = ttk.Scrollbar(self, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        canvas.pack(fill='both', expand=True, padx=10)

        inner = tk.Frame(canvas, bg=C['bg'])
        win = canvas.create_window((0,0), window=inner, anchor='nw')
        inner.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(win, width=e.width))

        e = self.entree
        self.vars = {}

        sections = [
            ("⚖️ Corps", [
                ('poids',           'Poids (kg)',               str(e.get('poids', '')),           'entry'),
                ('tour_taille',     'Tour de taille (cm)',      str(e.get('tour_taille', '')),      'entry'),
                ('tour_hanches',    'Tour de hanches (cm)',     str(e.get('tour_hanches', '')),     'entry'),
                ('tour_cou',        'Tour de cou (cm)',         str(e.get('tour_cou', '')),         'entry'),
                ('tour_bras',       'Tour de bras (cm)',        str(e.get('tour_bras', '')),        'entry'),
                ('tour_cuisse',     'Tour de cuisse (cm)',      str(e.get('tour_cuisse', '')),      'entry'),
            ]),
            ("💧 Hydratation & Énergie", [
                ('eau_litres',      'Eau bue (litres)',         str(e.get('eau_litres', '')),       'entry'),
                ('cafe_tasses',     'Cafés (nb tasses)',        str(e.get('cafe_tasses', '')),      'entry'),
                ('forme',           'Forme subjective (1-10)',  str(e.get('forme', '')),            'entry'),
                ('stress',          'Stress (1-10)',            str(e.get('stress', '')),           'entry'),
                ('faim',            'Faim générale (1-10)',     str(e.get('faim', '')),             'entry'),
            ]),
            ("😴 Sommeil", [
                ('sommeil_heures',  'Durée sommeil (h)',        str(e.get('sommeil_heures', '')),   'entry'),
                ('sommeil_qualite', 'Qualité sommeil (1-10)',   str(e.get('sommeil_qualite', '')),  'entry'),
                ('heure_coucher',   'Heure de coucher',         str(e.get('heure_coucher', '')),    'entry'),
                ('heure_lever',     'Heure de lever',           str(e.get('heure_lever', '')),      'entry'),
            ]),
            ("❤️ Cardio", [
                ('fc_repos',        'FC repos (bpm)',           str(e.get('fc_repos', '')),         'entry'),
                ('fc_max_mesure',   'FC max mesurée (bpm)',     str(e.get('fc_max_mesure', '')),    'entry'),
                ('tension_sys',     'Tension systolique',       str(e.get('tension_sys', '')),      'entry'),
                ('tension_dia',     'Tension diastolique',      str(e.get('tension_dia', '')),      'entry'),
            ]),
            ("🏋️ Entraînement", [
                ('seance',          'Séance du jour',           e.get('seance', ''),                'combo',
                 ['Repos', 'Musculation', 'Cardio', 'HIIT', 'Natation',
                  'Vélo', 'Course', 'Sport collectif', 'Yoga/Pilates', 'Autre']),
                ('duree_seance',    'Durée (minutes)',          str(e.get('duree_seance', '')),     'entry'),
                ('calories_brulees','Calories brûlées (kcal)',  str(e.get('calories_brulees', '')), 'entry'),
                ('rpe',             'Effort perçu RPE (1-10)',  str(e.get('rpe', '')),              'entry'),
            ]),
            ("📝 Notes", [
                ('notes',           'Notes libres',             e.get('notes', ''),                 'text'),
            ]),
        ]

        for titre, champs in sections:
            # Titre section
            sec = tk.Frame(inner, bg=C['surface2'], padx=16, pady=10)
            sec.pack(fill='x', padx=10, pady=(8, 2))
            tk.Label(sec, text=titre, bg=C['surface2'],
                     fg=C['text'], font=FONT_H3).pack(anchor='w')

            # Champs
            for item in champs:
                cle, label, val_def = item[0], item[1], item[2]
                type_w = item[3]

                row = tk.Frame(inner, bg=C['surface3'], padx=16, pady=6)
                row.pack(fill='x', padx=10, pady=1)

                tk.Label(row, text=label, bg=C['surface3'],
                         fg=C['text_muted'], font=FONT_LABEL, width=24,
                         anchor='w').pack(side='left')

                if type_w == 'entry':
                    var = tk.StringVar(value=val_def)
                    tk.Entry(row, textvariable=var,
                             bg=C['bg'], fg=C['text'],
                             insertbackground=C['accent'],
                             font=FONT_BODY, relief='flat', bd=4, width=14
                             ).pack(side='left', padx=(8, 0))
                    self.vars[cle] = var

                elif type_w == 'combo':
                    options = item[4]
                    var = tk.StringVar(value=val_def or options[0])
                    ttk.Combobox(row, textvariable=var, values=options,
                                 state='readonly', width=18).pack(side='left', padx=(8,0))
                    self.vars[cle] = var

                elif type_w == 'text':
                    var = tk.StringVar(value=val_def)
                    tk.Entry(row, textvariable=var,
                             bg=C['bg'], fg=C['text'],
                             insertbackground=C['accent'],
                             font=FONT_BODY, relief='flat', bd=4, width=28
                             ).pack(side='left', padx=(8, 0), fill='x', expand=True)
                    self.vars[cle] = var

        # Boutons fixes en bas
        btn_bar = tk.Frame(self, bg=C['bg'], pady=10)
        btn_bar.pack(fill='x', padx=20)
        tk.Button(btn_bar, text="Annuler", bg=C['surface2'], fg=C['text_muted'],
                  relief='flat', cursor='hand2', padx=14, pady=8,
                  activebackground=C['surface3'],
                  command=self.destroy).pack(side='right', padx=5)
        tk.Button(btn_bar, text="✓  Enregistrer",
                  bg=C['accent'], fg='white', font=FONT_BOLD,
                  relief='flat', cursor='hand2', padx=14, pady=8,
                  activebackground=C['accent_dim'],
                  command=self._valider).pack(side='right', padx=5)

    def _valider(self):
        def _float(k):
            try: return float(self.vars[k].get())
            except: return None
        def _int(k):
            try: return int(float(self.vars[k].get()))
            except: return None
        def _str(k):
            return self.vars[k].get().strip()

        entree = {
            'poids':           _float('poids'),
            'tour_taille':     _float('tour_taille'),
            'tour_hanches':    _float('tour_hanches'),
            'tour_cou':        _float('tour_cou'),
            'tour_bras':       _float('tour_bras'),
            'tour_cuisse':     _float('tour_cuisse'),
            'eau_litres':      _float('eau_litres'),
            'cafe_tasses':     _int('cafe_tasses'),
            'forme':           _int('forme'),
            'stress':          _int('stress'),
            'faim':            _int('faim'),
            'sommeil_heures':  _float('sommeil_heures'),
            'sommeil_qualite': _int('sommeil_qualite'),
            'heure_coucher':   _str('heure_coucher'),
            'heure_lever':     _str('heure_lever'),
            'fc_repos':        _int('fc_repos'),
            'fc_max_mesure':   _int('fc_max_mesure'),
            'tension_sys':     _int('tension_sys'),
            'tension_dia':     _int('tension_dia'),
            'seance':          _str('seance'),
            'duree_seance':    _int('duree_seance'),
            'calories_brulees':_int('calories_brulees'),
            'rpe':             _int('rpe'),
            'notes':           _str('notes'),
        }
        self.resultat = {k: v for k, v in entree.items() if v not in (None, '', 0)}
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE SANTÉ COMPLÈTE
# ═══════════════════════════════════════════════════════════════════════════════

class PageSante(tk.Frame):
    """Page santé complète avec toutes les métriques."""

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C['bg'], **kw)
        self._construire()

    def _construire(self):
        # En-tête
        header = tk.Frame(self, bg=C['bg'], pady=16)
        header.pack(fill='x', padx=30)
        tk.Label(header, text="🏥 Santé & Forme",
                 bg=C['bg'], fg=C['text'], font=FONT_TITLE).pack(side='left')

        btn_frame = tk.Frame(header, bg=C['bg'])
        btn_frame.pack(side='right')
        tk.Button(btn_frame, text="+ Saisir les mesures du jour",
                  bg=C['accent'], fg='white', font=FONT_BOLD,
                  relief='flat', cursor='hand2', padx=16, pady=9,
                  activebackground=C['accent_dim'],
                  command=self._ouvrir_saisie).pack(side='left', padx=5)
        tk.Button(btn_frame, text="🔄 Actualiser",
                  bg=C['surface2'], fg=C['text_muted'],
                  font=FONT_LABEL, relief='flat', cursor='hand2',
                  padx=12, pady=8,
                  command=self.actualiser).pack(side='left', padx=5)

        # Notebook
        nb = ttk.Notebook(self)
        nb.pack(fill='both', expand=True, padx=30, pady=(0, 20))

        self.tab_aujourdhui = tk.Frame(nb, bg=C['bg'])
        self.tab_poids      = tk.Frame(nb, bg=C['bg'])
        self.tab_corpo      = tk.Frame(nb, bg=C['bg'])
        self.tab_bien_etre  = tk.Frame(nb, bg=C['bg'])
        self.tab_historique = tk.Frame(nb, bg=C['bg'])

        nb.add(self.tab_aujourdhui, text="  📍 Aujourd'hui  ")
        nb.add(self.tab_poids,      text="  ⚖️ Poids  ")
        nb.add(self.tab_corpo,      text="  📐 Composition  ")
        nb.add(self.tab_bien_etre,  text="  😴 Bien-être  ")
        nb.add(self.tab_historique, text="  📋 Historique  ")

        from ui.main_window import ScrollFrame
        for tab in [self.tab_aujourdhui, self.tab_poids,
                    self.tab_corpo, self.tab_bien_etre, self.tab_historique]:
            sf = ScrollFrame(tab)
            sf.pack(fill='both', expand=True)
            setattr(self, f'_sf_{tab}', sf)
            setattr(self, f'_inner_{tab}', sf.inner)
            getattr(self, f'_inner_{tab}').configure(padx=10, pady=10)

        self.actualiser()

    def _get_profil(self):
        from database.db_manager import charger_profil
        p = charger_profil()
        return {'taille_cm': p.taille_cm, 'sexe': p.sexe, 'age': p.age,
                'poids_kg': p.poids_kg, 'activite': p.activite}

    def _ouvrir_saisie(self):
        profil = self._get_profil()
        entree_existante = charger_entree_jour()
        dialog = DialogSaisiesSante(self, profil, entree_existante)
        self.wait_window(dialog)
        if dialog.resultat:
            sauvegarder_entree(dialog.resultat)
            self.actualiser()
            messagebox.showinfo("Enregistré", "Mesures du jour sauvegardées !")

    def actualiser(self):
        profil   = self._get_profil()
        entrees  = charger_entrees_periode(30)
        aujourd  = charger_entree_jour()

        self._build_aujourdhui(aujourd, profil)
        self._build_poids(entrees, profil)
        self._build_corpo(entrees, profil, aujourd)
        self._build_bien_etre(entrees, aujourd)
        self._build_historique(entrees)

    # ── Onglet Aujourd'hui ────────────────────────────────────────────────────
    def _build_aujourdhui(self, e: dict, profil: dict):
        inner = self._inner_self_tab_aujourdhui()
        for w in inner.winfo_children(): w.destroy()

        if not e:
            vide = tk.Frame(inner, bg=C['surface2'], padx=30, pady=40)
            vide.pack(fill='x', pady=20)
            tk.Label(vide, text="Aucune mesure saisie aujourd'hui",
                     bg=C['surface2'], fg=C['text_muted'], font=FONT_H2).pack()
            tk.Label(vide, text="Clique sur '+ Saisir les mesures du jour'",
                     bg=C['surface2'], fg=C['text_muted'], font=FONT_LABEL).pack(pady=6)
            return

        # Calculs
        poids  = e.get('poids', profil['poids_kg'])
        taille = profil['taille_cm']
        sexe   = profil['sexe']
        age    = profil['age']

        imc = calcul_imc(poids, taille) if poids else 0
        cat_imc, col_imc = categorie_imc(imc) if imc else ("—", C['text_muted'])

        tc  = e.get('tour_cou', 0)
        tt  = e.get('tour_taille', 0)
        th  = e.get('tour_hanches', 0)
        mg  = calcul_masse_grasse_navy(taille, tc, tt, th, sexe) if tc and tt else 0
        cat_mg, col_mg = categorie_masse_grasse(mg, sexe) if mg else ("—", C['text_muted'])
        mm  = calcul_masse_maigre(poids, mg) if mg and poids else 0

        fc  = e.get('fc_repos', 0)
        vo2 = calcul_vo2max_estime(fc, age, sexe) if fc else 0
        cat_vo2, col_vo2 = categorie_vo2max(vo2, age, sexe) if vo2 else ("—", C['text_muted'])

        eau_obj = besoins_eau(poids, profil.get('activite', 'moderee'))
        eau_bu  = e.get('eau_litres', 0) or 0
        pct_eau = int(eau_bu / eau_obj * 100) if eau_obj else 0

        poids_id = poids_ideal_devine(taille, sexe)
        diff_poids = round((poids - poids_id), 1) if poids else 0

        # Cartes principales
        tk.Label(inner, text=f"Aujourd'hui — {date.today().strftime('%A %d %B %Y')}",
                 bg=C['bg'], fg=C['text_muted'], font=FONT_LABEL).pack(anchor='w', pady=(0, 10))

        grid1 = tk.Frame(inner, bg=C['bg'])
        grid1.pack(fill='x', pady=(0, 8))

        metriques = [
            ("⚖️ Poids",        f"{poids:.1f} kg" if poids else "—",    C['accent'],  f"Idéal : {poids_id} kg  ({'+' if diff_poids>0 else ''}{diff_poids} kg)"),
            ("📊 IMC",           f"{imc:.1f}" if imc else "—",           col_imc,      cat_imc),
            ("🫀 FC repos",      f"{fc} bpm" if fc else "—",             C['cal'],     f"VO2max est. : {vo2}" if vo2 else "Non calculé"),
            ("🏃 VO2max est.",   f"{vo2}" if vo2 else "—",               col_vo2,      cat_vo2),
            ("💪 Masse grasse",  f"{mg:.1f}%" if mg else "—",            col_mg,       cat_mg),
            ("🦴 Masse maigre",  f"{mm:.1f} kg" if mm else "—",          C['prot'],    f"Muscle + os + eau"),
        ]
        for i, (titre, valeur, couleur, sous_titre) in enumerate(metriques):
            col = i % 3; row = i // 3
            card = tk.Frame(grid1, bg=C['surface2'], padx=16, pady=14)
            card.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
            grid1.columnconfigure(col, weight=1)
            tk.Label(card, text=titre, bg=C['surface2'],
                     fg=C['text_muted'], font=FONT_SMALL).pack(anchor='w')
            tk.Label(card, text=valeur, bg=C['surface2'],
                     fg=couleur, font=FONT_NUM).pack(anchor='w')
            tk.Label(card, text=sous_titre, bg=C['surface2'],
                     fg=C['text_muted'], font=FONT_SMALL).pack(anchor='w')

        # Hydratation
        hyd = tk.Frame(inner, bg=C['surface2'], padx=20, pady=14)
        hyd.pack(fill='x', pady=(0, 8))
        tk.Label(hyd, text="💧 Hydratation",
                 bg=C['surface2'], fg=C['text'], font=FONT_H3).pack(anchor='w', pady=(0,8))

        row_eau = tk.Frame(hyd, bg=C['surface2'])
        row_eau.pack(fill='x')
        tk.Label(row_eau, text=f"{eau_bu:.1f}L bu  /  objectif {eau_obj:.1f}L",
                 bg=C['surface2'], fg=C['info'], font=FONT_NUM_SM).pack(side='left')
        col_eau = C['success'] if pct_eau >= 80 else (C['warning'] if pct_eau >= 50 else C['danger'])
        tk.Label(row_eau, text=f"{pct_eau}%",
                 bg=C['surface2'], fg=col_eau, font=FONT_NUM_SM).pack(side='right')

        # Barre eau
        cv_eau = tk.Canvas(hyd, height=10, bg=C['surface3'], highlightthickness=0)
        cv_eau.pack(fill='x', pady=(6,0))

        def _draw_eau(e2=None, cv=cv_eau, pct=pct_eau, col=col_eau):
            cv.delete('all')
            w = cv.winfo_width() or 400
            fill_w = int(w * min(pct/100, 1.0))
            r = 5
            cv.create_rectangle(0, 0, w, 10, fill=C['surface3'], outline='')
            if fill_w > 0:
                cv.create_rectangle(0, 0, fill_w, 10, fill=col, outline='')
        cv_eau.bind('<Configure>', _draw_eau)

        # Forme / Sommeil / Stress
        bien_etre = tk.Frame(inner, bg=C['surface2'], padx=20, pady=14)
        bien_etre.pack(fill='x', pady=(0, 8))
        tk.Label(bien_etre, text="😊 Bien-être du jour",
                 bg=C['surface2'], fg=C['text'], font=FONT_H3).pack(anchor='w', pady=(0,8))

        grid_be = tk.Frame(bien_etre, bg=C['surface2'])
        grid_be.pack(fill='x')
        items_be = [
            ("😴 Sommeil",  f"{e.get('sommeil_heures','—')}h",  f"Qualité : {e.get('sommeil_qualite','—')}/10"),
            ("💪 Forme",    f"{e.get('forme','—')}/10",          ""),
            ("😰 Stress",   f"{e.get('stress','—')}/10",         ""),
            ("☕ Cafés",    f"{e.get('cafe_tasses','—')} tasses",""),
            ("🏋️ Séance",  str(e.get('seance','Repos')),         f"{e.get('duree_seance','—')} min"),
            ("🔥 Brûlées", f"{e.get('calories_brulees','—')} kcal", ""),
        ]
        for i, (titre, valeur, detail) in enumerate(items_be):
            col = i % 3; row = i // 3
            card2 = tk.Frame(grid_be, bg=C['surface3'], padx=12, pady=10)
            card2.grid(row=row, column=col, padx=4, pady=4, sticky='ew')
            grid_be.columnconfigure(col, weight=1)
            tk.Label(card2, text=titre, bg=C['surface3'],
                     fg=C['text_muted'], font=FONT_SMALL).pack(anchor='w')
            tk.Label(card2, text=valeur, bg=C['surface3'],
                     fg=C['text'], font=FONT_NUM_SM).pack(anchor='w')
            if detail:
                tk.Label(card2, text=detail, bg=C['surface3'],
                         fg=C['text_muted'], font=FONT_SMALL).pack(anchor='w')

        # Notes
        if e.get('notes'):
            note_f = tk.Frame(inner, bg=C['surface3'], padx=16, pady=12)
            note_f.pack(fill='x', pady=(0, 8))
            tk.Label(note_f, text="📝 Notes du jour", bg=C['surface3'],
                     fg=C['text_muted'], font=FONT_SMALL).pack(anchor='w')
            tk.Label(note_f, text=e['notes'], bg=C['surface3'],
                     fg=C['text'], font=FONT_BODY, wraplength=600,
                     justify='left').pack(anchor='w', pady=(4, 0))

    def _inner_self_tab_aujourdhui(self):
        return self._inner_self.tab_aujourdhui if hasattr(self, '_inner_self') \
               else getattr(self, f'_inner_{self.tab_aujourdhui}')

    # ── Onglet Poids ──────────────────────────────────────────────────────────
    def _build_poids(self, entrees, profil):
        inner = getattr(self, f'_inner_{self.tab_poids}')
        for w in inner.winfo_children(): w.destroy()

        tk.Label(inner, text="Évolution du poids sur 30 jours",
                 bg=C['bg'], fg=C['text'], font=FONT_H2).pack(anchor='w', pady=(0,10))

        card_g = tk.Frame(inner, bg=C['surface2'], padx=12, pady=12)
        card_g.pack(fill='x', pady=(0, 10))
        GraphiquePoids(card_g, entrees, profil['taille_cm'],
                       profil['sexe'], height=220).pack(fill='x')

        # Stats poids
        poids_vals = [(d, e['poids']) for d, e in entrees if e.get('poids')]
        if poids_vals:
            vals = [p for _, p in poids_vals]
            stats = tk.Frame(inner, bg=C['surface2'], padx=20, pady=14)
            stats.pack(fill='x', pady=(0, 10))
            tk.Label(stats, text="Statistiques poids",
                     bg=C['surface2'], fg=C['text'], font=FONT_H3).pack(anchor='w', pady=(0,8))

            grid_s = tk.Frame(stats, bg=C['surface2'])
            grid_s.pack(fill='x')
            poids_id = poids_ideal_devine(profil['taille_cm'], profil['sexe'])
            dernier  = vals[-1]
            premier  = vals[0]
            delta    = round(dernier - premier, 1)

            items_s = [
                ("Actuel",       f"{dernier:.1f} kg",   C['accent']),
                ("Minimum",      f"{min(vals):.1f} kg", C['success']),
                ("Maximum",      f"{max(vals):.1f} kg", C['danger']),
                ("Moyenne",      f"{sum(vals)/len(vals):.1f} kg", C['text']),
                ("Évolution",    f"{'+' if delta>0 else ''}{delta} kg",
                                 C['danger'] if delta > 0 else C['success']),
                ("Poids idéal",  f"{poids_id} kg",      C['prot']),
            ]
            for i, (titre, valeur, couleur) in enumerate(items_s):
                col = i % 3; row = i // 3
                card_s = tk.Frame(grid_s, bg=C['surface3'], padx=12, pady=10)
                card_s.grid(row=row, column=col, padx=4, pady=4, sticky='ew')
                grid_s.columnconfigure(col, weight=1)
                tk.Label(card_s, text=titre, bg=C['surface3'],
                         fg=C['text_muted'], font=FONT_SMALL).pack(anchor='w')
                tk.Label(card_s, text=valeur, bg=C['surface3'],
                         fg=couleur, font=FONT_NUM_SM).pack(anchor='w')

    # ── Onglet Composition ────────────────────────────────────────────────────
    def _build_corpo(self, entrees, profil, aujourd):
        inner = getattr(self, f'_inner_{self.tab_corpo}')
        for w in inner.winfo_children(): w.destroy()

        tk.Label(inner, text="Composition corporelle",
                 bg=C['bg'], fg=C['text'], font=FONT_H2).pack(anchor='w', pady=(0,10))

        e = aujourd
        if not e:
            tk.Label(inner, text="Saisie des mesures requise pour calculer la composition.",
                     bg=C['bg'], fg=C['text_muted'], font=FONT_LABEL).pack(pady=30)
            return

        poids  = e.get('poids', profil['poids_kg'])
        taille = profil['taille_cm']
        sexe   = profil['sexe']
        tc = e.get('tour_cou', 0)
        tt = e.get('tour_taille', 0)
        th = e.get('tour_hanches', 0)

        mg  = calcul_masse_grasse_navy(taille, tc, tt, th, sexe) if tc and tt else 0
        mm  = calcul_masse_maigre(poids, mg) if mg and poids else 0
        cat_mg, col_mg = categorie_masse_grasse(mg, sexe) if mg else ("—", C['text_muted'])

        # Cercle visuel masse grasse (simulé en Canvas)
        cv_mg = tk.Canvas(inner, width=200, height=200,
                          bg=C['bg'], highlightthickness=0)
        cv_mg.pack(pady=(0, 10))

        def _draw_mg(e2=None):
            cv_mg.delete('all')
            cx, cy, r = 100, 100, 75
            # Fond
            cv_mg.create_oval(cx-r, cy-r, cx+r, cy+r,
                               fill=C['surface2'], outline=C['border'], width=2)
            # Arc masse grasse
            if mg > 0:
                angle = min(mg/100*360, 360)
                cv_mg.create_arc(cx-r, cy-r, cx+r, cy+r,
                                  start=90, extent=-angle,
                                  fill=col_mg, outline='')
            # Cercle central (donut)
            ri = 50
            cv_mg.create_oval(cx-ri, cy-ri, cx+ri, cy+ri,
                               fill=C['bg'], outline='')
            # Texte
            cv_mg.create_text(cx, cy-10, text=f"{mg:.1f}%",
                               fill=C['text'], font=('Segoe UI Semibold', 16, 'bold'))
            cv_mg.create_text(cx, cy+12, text="Masse grasse",
                               fill=C['text_muted'], font=FONT_SMALL)
        cv_mg.bind('<Configure>', _draw_mg)
        _draw_mg()

        # Métriques corporelles
        grid_c = tk.Frame(inner, bg=C['bg'])
        grid_c.pack(fill='x', pady=(0, 10))

        metriques_c = [
            ("💪 Masse grasse",   f"{mg:.1f}%" if mg else "—",  col_mg,        cat_mg),
            ("🦴 Masse maigre",   f"{mm:.1f} kg" if mm else "—", C['prot'],    "Muscles + os + eau"),
            ("📏 Tour taille",    f"{tt:.0f} cm" if tt else "—", C['gluc'],    "Risque si >94cm (H) / >80cm (F)"),
            ("📐 Tour hanches",   f"{th:.0f} cm" if th else "—", C['accent'],  ""),
            ("💪 Tour bras",      f"{e.get('tour_bras','—')} cm", C['cal'],    ""),
            ("🦵 Tour cuisse",    f"{e.get('tour_cuisse','—')} cm", C['lip'],  ""),
        ]
        for i, (titre, valeur, couleur, detail) in enumerate(metriques_c):
            col_i = i % 2; row_i = i // 2
            card_c = tk.Frame(grid_c, bg=C['surface2'], padx=16, pady=12)
            card_c.grid(row=row_i, column=col_i, padx=5, pady=5, sticky='ew')
            grid_c.columnconfigure(col_i, weight=1)
            tk.Label(card_c, text=titre, bg=C['surface2'],
                     fg=C['text_muted'], font=FONT_SMALL).pack(anchor='w')
            tk.Label(card_c, text=valeur, bg=C['surface2'],
                     fg=couleur, font=FONT_NUM_SM).pack(anchor='w')
            if detail:
                tk.Label(card_c, text=detail, bg=C['surface2'],
                         fg=C['text_muted'], font=FONT_SMALL).pack(anchor='w')

    # ── Onglet Bien-être ──────────────────────────────────────────────────────
    def _build_bien_etre(self, entrees, aujourd):
        inner = getattr(self, f'_inner_{self.tab_bien_etre}')
        for w in inner.winfo_children(): w.destroy()

        tk.Label(inner, text="Suivi bien-être & sommeil sur 30 jours",
                 bg=C['bg'], fg=C['text'], font=FONT_H2).pack(anchor='w', pady=(0,10))

        # Moyennes bien-être
        metriques_be = [
            ('forme',          '💪 Forme',    '/10', C['prot']),
            ('stress',         '😰 Stress',   '/10', C['cal']),
            ('sommeil_heures', '😴 Sommeil',  'h',   C['accent']),
            ('sommeil_qualite','🛏️ Qualité',  '/10', C['info']),
            ('eau_litres',     '💧 Eau',      'L',   C['info']),
            ('fc_repos',       '🫀 FC repos', 'bpm', C['cal']),
        ]

        grid_be = tk.Frame(inner, bg=C['bg'])
        grid_be.pack(fill='x', pady=(0, 10))

        for i, (cle, titre, unite, couleur) in enumerate(metriques_be):
            vals = [e[cle] for _, e in entrees if e.get(cle)]
            moy  = sum(vals)/len(vals) if vals else None

            col_i = i % 3; row_i = i // 3
            card_b = tk.Frame(grid_be, bg=C['surface2'], padx=16, pady=12)
            card_b.grid(row=row_i, column=col_i, padx=5, pady=5, sticky='ew')
            grid_be.columnconfigure(col_i, weight=1)

            tk.Label(card_b, text=titre, bg=C['surface2'],
                     fg=C['text_muted'], font=FONT_SMALL).pack(anchor='w')
            txt = f"{moy:.1f}{unite}" if moy else "—"
            tk.Label(card_b, text=txt, bg=C['surface2'],
                     fg=couleur, font=FONT_NUM_SM).pack(anchor='w')
            tk.Label(card_b, text=f"sur {len(vals)} jours",
                     bg=C['surface2'], fg=C['text_muted'], font=FONT_SMALL).pack(anchor='w')

    # ── Onglet Historique ─────────────────────────────────────────────────────
    def _build_historique(self, entrees):
        inner = getattr(self, f'_inner_{self.tab_historique}')
        for w in inner.winfo_children(): w.destroy()

        tk.Label(inner, text="Historique des mesures",
                 bg=C['bg'], fg=C['text'], font=FONT_H2).pack(anchor='w', pady=(0,10))

        cols = ('date', 'poids', 'imc', 'mg', 'eau', 'forme', 'sommeil', 'fc', 'seance')
        tree = ttk.Treeview(inner, columns=cols, show='headings', height=18)
        for col, label, w in [
            ('date',    'Date',     100), ('poids',  'Poids',  80),
            ('imc',     'IMC',       65), ('mg',     'MG%',    65),
            ('eau',     'Eau',       65), ('forme',  'Forme',  60),
            ('sommeil', 'Sommeil',   70), ('fc',     'FC',     65),
            ('seance',  'Séance',   130),
        ]:
            tree.heading(col, text=label)
            tree.column(col, width=w, anchor='center')

        from database.db_manager import charger_profil
        profil = charger_profil()

        for d, e in reversed(entrees):
            poids  = e.get('poids', '')
            imc_v  = calcul_imc(poids, profil.taille_cm) if poids else ''
            tc     = e.get('tour_cou', 0)
            tt     = e.get('tour_taille', 0)
            th     = e.get('tour_hanches', 0)
            mg_v   = calcul_masse_grasse_navy(profil.taille_cm, tc, tt, th,
                                              profil.sexe) if tc and tt else ''
            mois_fr = ['Jan','Fev','Mar','Avr','Mai','Jun',
                       'Jul','Aou','Sep','Oct','Nov','Dec']
            date_str = f"{d.day} {mois_fr[d.month-1]} {d.year}"
            tree.insert('', 0, values=(
                date_str,
                f"{poids:.1f}" if poids else "—",
                f"{imc_v:.1f}" if imc_v else "—",
                f"{mg_v:.1f}%" if mg_v else "—",
                f"{e.get('eau_litres','—')}L",
                f"{e.get('forme','—')}/10",
                f"{e.get('sommeil_heures','—')}h",
                f"{e.get('fc_repos','—')}",
                e.get('seance', '—'),
            ))

        sc = ttk.Scrollbar(inner, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=sc.set)

        def _wheel_h(ev): tree.yview_scroll(int(-1*(ev.delta/120)), 'units')
        tree.bind('<MouseWheel>', _wheel_h)

        sc.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True)

    # ── Helper inner frames ───────────────────────────────────────────────────
    def __getattr__(self, name):
        # Proxy pour accéder aux inner frames des onglets
        if name.startswith('_inner_'):
            tab = name[len('_inner_'):]
            sf_name = f'_sf_{tab}'
            if hasattr(self, sf_name):
                return getattr(self, sf_name).inner
        raise AttributeError(name)
