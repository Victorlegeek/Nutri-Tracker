# ui/graphiques.py
# Graphiques dessinés en tkinter Canvas pur — aucune dépendance externe

import tkinter as tk
from tkinter import ttk
from datetime import date, timedelta
import sys, os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database.db_manager import charger_journal, charger_objectifs, calculer_totaux

# ─── PALETTE ──────────────────────────────────────────────────────────────────
C = {
    'bg':         '#0e0e12',
    'surface':    '#16161d',
    'surface2':   '#1e1e27',
    'surface3':   '#26262f',
    'border':     '#252530',
    'text':       '#f0f0f5',
    'text_muted': '#6b7280',
    'accent':     '#7c6aff',
    'success':    '#22c55e',
    'warning':    '#f59e0b',
    'danger':     '#ef4444',
    'cal':        '#ff6b81',
    'prot':       '#4ade80',
    'gluc':       '#fbbf24',
    'lip':        '#a78bfa',
    'fibres':     '#34d399',
    'grid':       '#1e1e2e',
}

FONT_SMALL  = ('Segoe UI', 8)
FONT_LABEL  = ('Segoe UI', 9)
FONT_BOLD   = ('Segoe UI', 10, 'bold')
FONT_H2     = ('Segoe UI', 12, 'bold')
FONT_TITLE  = ('Segoe UI Semibold', 14, 'bold')


def _charger_donnees_periode(nb_jours: int) -> list[dict]:
    """Retourne une liste de dicts {date, calories, proteines, glucides, lipides, fibres}"""
    today = date.today()
    resultats = []
    for i in range(nb_jours - 1, -1, -1):
        d = today - timedelta(days=i)
        entrees = charger_journal(d)
        if entrees:
            t = calculer_totaux(entrees)
            resultats.append({
                'date':     d,
                'calories': t.calories,
                'proteines': t.proteines,
                'glucides':  t.glucides,
                'lipides':   t.lipides,
                'fibres':    t.fibres,
                'sel':       t.sel,
            })
        else:
            resultats.append({
                'date':     d,
                'calories': None,
                'proteines': None,
                'glucides':  None,
                'lipides':   None,
                'fibres':    None,
                'sel':       None,
            })
    return resultats


# ═══════════════════════════════════════════════════════════════════════════════
# WIDGET GRAPHE COURBE
# ═══════════════════════════════════════════════════════════════════════════════

class GraphiqueCourbe(tk.Canvas):
    """
    Canvas qui dessine une courbe lisse avec grille, axes, légende et objectif.
    """
    PAD_L = 55   # marge gauche (axe Y)
    PAD_R = 20
    PAD_T = 20
    PAD_B = 45   # marge bas (axe X)

    def __init__(self, parent, donnees: list, cle: str, couleur: str,
                 label: str, objectif: float = None, unite: str = '',
                 height=220, **kw):
        super().__init__(parent, bg=C['bg'], highlightthickness=0,
                         height=height, **kw)
        self.donnees  = donnees
        self.cle      = cle
        self.couleur  = couleur
        self.label    = label
        self.objectif = objectif
        self.unite    = unite
        self.bind('<Configure>', lambda e: self._dessiner())

    def _dessiner(self):
        self.delete('all')
        W = self.winfo_width()
        H = self.winfo_height()
        if W < 10 or H < 10:
            return

        pl, pr, pt, pb = self.PAD_L, self.PAD_R, self.PAD_T, self.PAD_B
        w_graph = W - pl - pr
        h_graph = H - pt - pb

        # Valeurs présentes seulement
        valeurs = [d[self.cle] for d in self.donnees if d[self.cle] is not None]
        if not valeurs:
            self.create_text(W//2, H//2, text="Pas encore de données",
                             fill=C['text_muted'], font=FONT_LABEL)
            return

        val_max = max(valeurs) * 1.15
        if self.objectif:
            val_max = max(val_max, self.objectif * 1.1)
        val_max = val_max or 1

        # ── Grille horizontale ────────────────────────────────────────────────
        nb_lignes = 5
        for i in range(nb_lignes + 1):
            y = pt + h_graph - (i / nb_lignes) * h_graph
            val_y = (i / nb_lignes) * val_max
            self.create_line(pl, y, W - pr, y, fill=C['grid'], width=1)
            label_y = f"{val_y:.0f}" if val_y >= 10 else f"{val_y:.1f}"
            self.create_text(pl - 6, y, text=label_y,
                             fill=C['text_muted'], font=FONT_SMALL, anchor='e')

        # ── Ligne objectif ────────────────────────────────────────────────────
        if self.objectif and self.objectif > 0:
            y_obj = pt + h_graph - (self.objectif / val_max) * h_graph
            # Ligne pointillée simulée
            for x in range(pl, W - pr, 8):
                self.create_line(x, y_obj, min(x+4, W-pr), y_obj,
                                 fill=self.couleur, width=1,
                                 dash=(4, 4))
            self.create_text(W - pr - 2, y_obj - 7,
                             text=f"Obj. {self.objectif:.0f}{self.unite}",
                             fill=self.couleur, font=FONT_SMALL, anchor='e')

        # ── Calcul des points ─────────────────────────────────────────────────
        n = len(self.donnees)
        points = []
        for i, d in enumerate(self.donnees):
            x = pl + (i / max(n - 1, 1)) * w_graph
            if d[self.cle] is not None:
                y = pt + h_graph - (d[self.cle] / val_max) * h_graph
                points.append((x, y, d['date'], d[self.cle]))
            else:
                points.append((x, None, d['date'], None))

        # ── Aire sous la courbe ───────────────────────────────────────────────
        pts_valides = [(x, y) for x, y, _, v in points if y is not None]
        if len(pts_valides) >= 2:
            # Construire le polygone fermé
            poly = []
            for x, y in pts_valides:
                poly.extend([x, y])
            # Fermer par le bas
            poly.extend([pts_valides[-1][0], pt + h_graph])
            poly.extend([pts_valides[0][0],  pt + h_graph])
            self.create_polygon(poly, fill=self.couleur,
                                stipple='gray25', outline='', smooth=True)

        # ── Courbe principale ─────────────────────────────────────────────────
        segments = []
        current = []
        for x, y, d, v in points:
            if y is not None:
                current.append((x, y))
            else:
                if len(current) >= 2:
                    segments.append(current)
                current = []
        if len(current) >= 2:
            segments.append(current)

        for seg in segments:
            coords = []
            for x, y in seg:
                coords.extend([x, y])
            self.create_line(coords, fill=self.couleur, width=2,
                             smooth=True, capstyle='round', joinstyle='round')

        # ── Points + tooltip ──────────────────────────────────────────────────
        for x, y, d, v in points:
            if y is None:
                continue
            # Cercle blanc au centre
            r = 4
            self.create_oval(x-r, y-r, x+r, y+r,
                             fill=C['bg'], outline=self.couleur, width=2)
            # Valeur au survol (simplifiée : on affiche au-dessus du point)
            # On affiche uniquement pour le dernier point et le max
            if v == max(valeurs) or x == points[-1][0]:
                self.create_text(x, y - 12, text=f"{v:.0f}",
                                 fill=C['text'], font=FONT_SMALL)

        # ── Axe X (dates) ─────────────────────────────────────────────────────
        mois_fr = ['Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Jun',
                   'Jul', 'Aou', 'Sep', 'Oct', 'Nov', 'Dec']
        # Afficher max 7 labels pour éviter chevauchement
        step = max(1, n // 7)
        for i, (x, y, d, v) in enumerate(points):
            if i % step == 0 or i == n - 1:
                label_x = f"{d.day} {mois_fr[d.month-1]}"
                self.create_text(x, H - pb + 12, text=label_x,
                                 fill=C['text_muted'], font=FONT_SMALL)

        # ── Titre ─────────────────────────────────────────────────────────────
        self.create_text(pl, pt - 5, text=self.label,
                         fill=self.couleur, font=FONT_BOLD, anchor='w')

        # Valeur moyenne
        moy = sum(valeurs) / len(valeurs)
        self.create_text(W - pr, pt - 5,
                         text=f"moy. {moy:.0f}{self.unite}",
                         fill=C['text_muted'], font=FONT_SMALL, anchor='e')


# ═══════════════════════════════════════════════════════════════════════════════
# WIDGET BARRES COMPARATIVES (semaine)
# ═══════════════════════════════════════════════════════════════════════════════

class GraphiqueBarres(tk.Canvas):
    """Graphique en barres groupées pour comparer les macros sur la semaine."""

    PAD_L = 45
    PAD_R = 15
    PAD_T = 20
    PAD_B = 40

    def __init__(self, parent, donnees: list, height=200, **kw):
        super().__init__(parent, bg=C['bg'], highlightthickness=0,
                         height=height, **kw)
        self.donnees = donnees
        self.bind('<Configure>', lambda e: self._dessiner())

    def _dessiner(self):
        self.delete('all')
        W = self.winfo_width()
        H = self.winfo_height()
        if W < 10 or H < 10:
            return

        pl, pr, pt, pb = self.PAD_L, self.PAD_R, self.PAD_T, self.PAD_B
        w_graph = W - pl - pr
        h_graph = H - pt - pb

        obj = charger_objectifs()
        macros = [
            ('calories',  C['cal'],    obj.get('calories', 2000),  'kcal'),
            ('proteines', C['prot'],   obj.get('proteines', 150),  'g'),
            ('glucides',  C['gluc'],   obj.get('glucides', 200),   'g'),
            ('lipides',   C['lip'],    obj.get('lipides', 65),     'g'),
        ]

        # Données des 7 derniers jours avec valeur (ignorer jours vides)
        jours_data = [d for d in self.donnees if d['calories'] is not None]
        if not jours_data:
            self.create_text(W//2, H//2, text="Pas encore de données",
                             fill=C['text_muted'], font=FONT_LABEL)
            return

        n_jours = len(jours_data)
        n_macros = len(macros)
        groupe_w = w_graph / max(n_jours, 1)
        barre_w  = max(4, (groupe_w - 8) / n_macros)

        # Grille
        for i in range(6):
            y = pt + (i / 5) * h_graph
            self.create_line(pl, y, W - pr, y, fill=C['grid'], width=1)
            pct = 100 - i * 20
            self.create_text(pl - 4, y, text=f"{pct}%",
                             fill=C['text_muted'], font=FONT_SMALL, anchor='e')

        # Barres
        mois_fr = ['Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Jun',
                   'Jul', 'Aou', 'Sep', 'Oct', 'Nov', 'Dec']
        for j, jour in enumerate(jours_data):
            x_groupe = pl + j * groupe_w + 4
            for m, (cle, couleur, objectif, unite) in enumerate(macros):
                val = jour[cle] or 0
                pct = min(val / objectif, 1.3) if objectif else 0
                x1 = x_groupe + m * barre_w
                y1 = pt + h_graph - pct * h_graph
                y2 = pt + h_graph
                # Couleur rouge si dépassé
                col = couleur if pct <= 1.0 else C['danger']
                # Barre avec coins arrondis (simulé)
                self.create_rectangle(x1, y1, x1 + barre_w - 1, y2,
                                      fill=col, outline='', width=0)
            # Label date
            d = jour['date']
            label_d = f"{d.day}/{d.month}"
            self.create_text(x_groupe + (n_macros * barre_w) / 2,
                             H - pb + 12, text=label_d,
                             fill=C['text_muted'], font=FONT_SMALL)

        # Légende
        lx = pl
        for cle, couleur, _, label in macros:
            self.create_rectangle(lx, H - 12, lx + 10, H - 4,
                                  fill=couleur, outline='')
            nom = {'calories': 'Cal.', 'proteines': 'Prot.',
                   'glucides': 'Gluc.', 'lipides': 'Lip.'}[cle]
            self.create_text(lx + 14, H - 8, text=nom,
                             fill=C['text_muted'], font=FONT_SMALL, anchor='w')
            lx += 60


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE GRAPHIQUES COMPLÈTE
# ═══════════════════════════════════════════════════════════════════════════════

class PageGraphiques(tk.Frame):
    """Page complète avec onglets 7j / 30j / comparaison."""

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C['bg'], **kw)
        self._construire()

    def _construire(self):
        # En-tête
        header = tk.Frame(self, bg=C['bg'], pady=16)
        header.pack(fill='x', padx=30)
        tk.Label(header, text="📈 Graphiques de progression",
                 bg=C['bg'], fg=C['text'],
                 font=FONT_TITLE).pack(side='left')
        tk.Button(header, text="🔄 Actualiser",
                  bg=C['surface2'], fg=C['text_muted'],
                  font=FONT_LABEL, relief='flat', cursor='hand2',
                  padx=12, pady=6,
                  command=self.actualiser).pack(side='right')

        # Sélecteur période
        ctrl = tk.Frame(self, bg=C['bg'], padx=30)
        ctrl.pack(fill='x', pady=(0, 10))

        tk.Label(ctrl, text="Période :", bg=C['bg'],
                 fg=C['text_muted'], font=FONT_LABEL).pack(side='left')

        self.var_periode = tk.IntVar(value=7)
        for label, val in [("7 jours", 7), ("14 jours", 14), ("30 jours", 30)]:
            tk.Radiobutton(ctrl, text=label, variable=self.var_periode,
                           value=val, bg=C['bg'], fg=C['text_muted'],
                           selectcolor=C['surface2'],
                           activebackground=C['bg'],
                           font=FONT_LABEL, cursor='hand2',
                           command=self.actualiser).pack(side='left', padx=10)

        # Notebook onglets
        nb = ttk.Notebook(self)
        nb.pack(fill='both', expand=True, padx=30, pady=(0, 20))

        self.tab_courbes  = tk.Frame(nb, bg=C['bg'])
        self.tab_barres   = tk.Frame(nb, bg=C['bg'])
        self.tab_resume   = tk.Frame(nb, bg=C['bg'])

        nb.add(self.tab_courbes, text='  📈 Courbes  ')
        nb.add(self.tab_barres,  text='  📊 Barres  ')
        nb.add(self.tab_resume,  text='  🧮 Résumé  ')

        # Scroll dans chaque onglet
        from ui.main_window import ScrollFrame
        sf1 = ScrollFrame(self.tab_courbes)
        sf1.pack(fill='both', expand=True)
        self.inner_courbes = sf1.inner
        self.inner_courbes.configure(padx=10, pady=10)

        sf2 = ScrollFrame(self.tab_barres)
        sf2.pack(fill='both', expand=True)
        self.inner_barres = sf2.inner
        self.inner_barres.configure(padx=10, pady=10)

        sf3 = ScrollFrame(self.tab_resume)
        sf3.pack(fill='both', expand=True)
        self.inner_resume = sf3.inner
        self.inner_resume.configure(padx=10, pady=10)

        self.actualiser()

    def actualiser(self):
        nb_jours = self.var_periode.get()
        donnees  = _charger_donnees_periode(nb_jours)
        obj      = charger_objectifs()

        self._construire_courbes(donnees, obj)
        self._construire_barres(donnees)
        self._construire_resume(donnees, obj)

    # ── Onglet Courbes ────────────────────────────────────────────────────────
    def _construire_courbes(self, donnees, obj):
        for w in self.inner_courbes.winfo_children():
            w.destroy()

        macros_courbes = [
            ('calories',  C['cal'],    '🔥 Calories',   obj.get('calories', 2000),  'kcal'),
            ('proteines', C['prot'],   '💪 Protéines',  obj.get('proteines', 150),  'g'),
            ('glucides',  C['gluc'],   '🌾 Glucides',   obj.get('glucides', 200),   'g'),
            ('lipides',   C['lip'],    '🫒 Lipides',    obj.get('lipides', 65),     'g'),
            ('fibres',    C['fibres'], '🌿 Fibres',     obj.get('fibres', 25),      'g'),
        ]

        for cle, couleur, label, objectif, unite in macros_courbes:
            # Carte conteneur
            card = tk.Frame(self.inner_courbes, bg=C['surface2'], padx=12, pady=12)
            card.pack(fill='x', pady=6)

            graphe = GraphiqueCourbe(
                card, donnees, cle=cle, couleur=couleur,
                label=label, objectif=objectif, unite=unite, height=200
            )
            graphe.pack(fill='x', expand=True)

    # ── Onglet Barres ─────────────────────────────────────────────────────────
    def _construire_barres(self, donnees):
        for w in self.inner_barres.winfo_children():
            w.destroy()

        tk.Label(self.inner_barres,
                 text="Comparaison macros vs objectif (% de l'objectif atteint)",
                 bg=C['bg'], fg=C['text_muted'],
                 font=FONT_LABEL).pack(anchor='w', pady=(0, 8))

        card = tk.Frame(self.inner_barres, bg=C['surface2'], padx=12, pady=12)
        card.pack(fill='x', pady=6)
        GraphiqueBarres(card, donnees[-7:], height=220).pack(fill='x')

        # Légende couleurs
        leg = tk.Frame(self.inner_barres, bg=C['bg'])
        leg.pack(fill='x', pady=(4, 12))
        for label, couleur in [
            ("En dessous de l'objectif", C['prot']),
            ("Objectif dépassé",         C['danger']),
        ]:
            row = tk.Frame(leg, bg=C['bg'])
            row.pack(side='left', padx=16)
            tk.Frame(row, bg=couleur, width=12, height=12).pack(side='left', padx=(0, 5))
            tk.Label(row, text=label, bg=C['bg'],
                     fg=C['text_muted'], font=FONT_SMALL).pack(side='left')

    # ── Onglet Résumé ─────────────────────────────────────────────────────────
    def _construire_resume(self, donnees, obj):
        for w in self.inner_resume.winfo_children():
            w.destroy()

        jours_valides = [d for d in donnees if d['calories'] is not None]
        n = len(jours_valides)

        if not jours_valides:
            tk.Label(self.inner_resume, text="Aucune donnée pour cette période.",
                     bg=C['bg'], fg=C['text_muted'],
                     font=FONT_LABEL).pack(pady=40)
            return

        tk.Label(self.inner_resume,
                 text=f"Résumé sur {n} jour(s) renseigné(s)",
                 bg=C['bg'], fg=C['text'],
                 font=FONT_H2).pack(anchor='w', pady=(0, 16))

        macros = [
            ('calories',  '🔥 Calories',  'kcal', C['cal']),
            ('proteines', '💪 Protéines', 'g',    C['prot']),
            ('glucides',  '🌾 Glucides',  'g',    C['gluc']),
            ('lipides',   '🫒 Lipides',   'g',    C['lip']),
            ('fibres',    '🌿 Fibres',    'g',    C['fibres']),
            ('sel',       '🧂 Sel',       'g',    C['text_muted']),
        ]

        grid = tk.Frame(self.inner_resume, bg=C['bg'])
        grid.pack(fill='x')

        for i, (cle, label, unite, couleur) in enumerate(macros):
            valeurs = [d[cle] for d in jours_valides if d[cle] is not None]
            moy  = sum(valeurs) / len(valeurs) if valeurs else 0
            mini = min(valeurs) if valeurs else 0
            maxi = max(valeurs) if valeurs else 0
            total = sum(valeurs)
            objectif = obj.get(cle, 0)
            pct_moy  = int(moy / objectif * 100) if objectif else 0
            col_pct  = C['success'] if 80 <= pct_moy <= 115 else (
                       C['danger'] if pct_moy > 115 else C['warning'])

            col  = i % 2
            row  = i // 2
            card = tk.Frame(grid, bg=C['surface2'], padx=16, pady=14)
            card.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
            grid.columnconfigure(col, weight=1)

            tk.Label(card, text=label, bg=C['surface2'],
                     fg=C['text_muted'], font=FONT_SMALL).pack(anchor='w')

            # Valeur moyenne grande
            tk.Label(card, text=f"{moy:.0f} {unite}",
                     bg=C['surface2'], fg=couleur,
                     font=('Segoe UI Semibold', 20, 'bold')).pack(anchor='w')

            # % objectif
            tk.Label(card, text=f"{pct_moy}% de l'objectif",
                     bg=C['surface2'], fg=col_pct,
                     font=FONT_SMALL).pack(anchor='w')

            # Stats mini / maxi / total
            stats_row = tk.Frame(card, bg=C['surface2'])
            stats_row.pack(fill='x', pady=(8, 0))
            for stat_label, val in [('Min', mini), ('Max', maxi), ('Total', total)]:
                col_f = tk.Frame(stats_row, bg=C['surface3'], padx=8, pady=4)
                col_f.pack(side='left', padx=(0, 4))
                tk.Label(col_f, text=stat_label, bg=C['surface3'],
                         fg=C['text_muted'], font=('Segoe UI', 7)).pack()
                tk.Label(col_f, text=f"{val:.0f}",
                         bg=C['surface3'], fg=C['text'],
                         font=('Segoe UI', 9, 'bold')).pack()

        # ── Streak & consistance ──────────────────────────────────────────────
        streak_frame = tk.Frame(self.inner_resume, bg=C['surface2'], padx=20, pady=16)
        streak_frame.pack(fill='x', pady=(12, 0))

        tk.Label(streak_frame, text="Régularité",
                 bg=C['surface2'], fg=C['text'],
                 font=FONT_H2).pack(anchor='w', pady=(0, 10))

        # Calcul streak (jours consécutifs renseignés depuis aujourd'hui)
        streak = 0
        today = date.today()
        for i in range(len(donnees)):
            d_check = today - timedelta(days=i)
            if charger_journal(d_check):
                streak += 1
            else:
                break

        consistance = int(n / self.var_periode.get() * 100)
        col_consist = C['success'] if consistance >= 70 else (
                      C['warning'] if consistance >= 40 else C['danger'])

        stats2 = tk.Frame(streak_frame, bg=C['surface2'])
        stats2.pack(fill='x')
        for s_label, s_val, s_col in [
            ("🔥 Streak actuel",   f"{streak} jour(s)",          C['cal']),
            ("📅 Jours renseignés", f"{n} / {self.var_periode.get()}",  C['accent']),
            ("✅ Consistance",      f"{consistance}%",             col_consist),
        ]:
            col_f = tk.Frame(stats2, bg=C['surface3'], padx=14, pady=10)
            col_f.pack(side='left', padx=(0, 6), expand=True, fill='x')
            tk.Label(col_f, text=s_label, bg=C['surface3'],
                     fg=C['text_muted'], font=FONT_SMALL).pack(anchor='w')
            tk.Label(col_f, text=s_val,   bg=C['surface3'],
                     fg=s_col, font=('Segoe UI Semibold', 16, 'bold')).pack(anchor='w')
