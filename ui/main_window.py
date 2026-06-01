"""
ui/main_window.py - Fenêtre principale de l'application
Interface thème sombre, menu latéral, journal journalier
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date, datetime, timedelta
import sys, os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database.db_manager import (
    charger_aliments, charger_journal, ajouter_entree_journal,
    supprimer_entree_journal, modifier_entree_journal,
    charger_objectifs, calculer_totaux, charger_profil,
    charger_dates_journal, basculer_favori, rechercher_aliment
)
from models.aliment import Aliment, EntreeJournal, ValeursNutritionnelles
from nutrition.analyse import analyser_aliment, score_sante, couleur_score, suggestions_alternatives, analyser_journee

# ─── PALETTE PROFESSIONNELLE (Moderne & Ergonomique) ──────────────────────────
C = {
    # Fonds
    'bg':           '#09090b',   # noir très profond (Tailwind zinc-950)
    'surface':      '#18181b',   # surface principale (zinc-900)
    'surface2':     '#27272a',   # surface secondaire (zinc-800)
    'surface3':     '#3f3f46',   # surface hover / input (zinc-700)
    'sidebar':      '#09090b',   # sidebar intégrée
    # Accent
    'accent':       '#6366f1',   # Indigo moderne
    'accent_dim':   '#4f46e5',   # Indigo focus press
    'accent2':      '#10b981',   # Emerald
    # Texte
    'text':         '#f4f4f5',   # zinc-50
    'text_muted':   '#a1a1aa',   # zinc-400
    'text_dim':     '#52525b',   # zinc-600
    # Sémantique
    'success':      '#22c55e',   # green-500
    'warning':      '#f59e0b',   # amber-500
    'danger':       '#ef4444',   # red-500
    'info':         '#38bdf8',   # sky-400
    # UI
    'border':       '#3f3f46',
    'border_light': '#52525b',
    'hover':        '#27272a',
    # Macros (couleurs douces et distinctes)
    'cal':          '#f43f5e',   # rose-500
    'prot':         '#3b82f6',   # blue-500
    'gluc':         '#eab308',   # yellow-500
    'lip':          '#8b5cf6',   # blue-violet
    'fibres':       '#10b981',   # emerald-500
    'sel_c':        '#9ca3af',   # gray
    'sucres_c':     '#ec4899',   # pink-500
}

FONT_TITLE  = ('Segoe UI', 24, 'bold')
FONT_H2     = ('Segoe UI', 14, 'bold')
FONT_H3     = ('Segoe UI', 12, 'bold')
FONT_BODY   = ('Segoe UI', 11)
FONT_SMALL  = ('Segoe UI', 10)
FONT_BOLD   = ('Segoe UI', 11, 'bold')
FONT_MONO   = ('Consolas', 11)
FONT_NUM    = ('Segoe UI', 20, 'bold')
FONT_NUM_LG = ('Segoe UI', 28, 'bold')

REPAS_OPTIONS = ["Petit-déjeuner", "Déjeuner", "Dîner", "Collation"]

# ─── HELPERS VISUELS ─────────────────────────────────────────────────────────
def rounded_rect(canvas, x1, y1, x2, y2, r=10, **kw):
    """Dessine un rectangle arrondi sur un Canvas."""
    pts = [
        x1+r, y1,   x2-r, y1,
        x2, y1,     x2, y1+r,
        x2, y2-r,   x2, y2,
        x2-r, y2,   x1+r, y2,
        x1, y2,     x1, y2-r,
        x1, y1+r,   x1, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


def make_card(parent, padx=16, pady=14, radius=10, bg=None):
    """
    Retourne un Frame avec fond arrondi simulé via Canvas.
    Utilisation : frame = make_card(parent); widgets -> frame
    """
    bg_col = bg or C['surface2']
    outer = tk.Frame(parent, bg=C['bg'])

    cv = tk.Canvas(outer, bg=C['bg'], highlightthickness=0)
    cv.pack(fill='both', expand=True)

    def _draw(event=None):
        cv.delete('all')
        w, h = cv.winfo_width(), cv.winfo_height()
        if w < 4 or h < 4:
            return
        rounded_rect(cv, 1, 1, w-1, h-1, r=radius,
                     fill=bg_col, outline=C['border'], width=1)

    cv.bind('<Configure>', _draw)

    inner = tk.Frame(cv, bg=bg_col)
    cv.create_window(padx, pady, anchor='nw', window=inner)

    def _resize(event=None):
        _draw()
        w, h = cv.winfo_width(), cv.winfo_height()
        inner.configure(width=max(1, w - padx*2),
                        height=max(1, h - pady*2))

    cv.bind('<Configure>', _resize)
    return outer, inner





class CustomScrollbar(tk.Canvas):
    """Scrollbar ultra-fine pill arrondie dessinée en Canvas."""
    W = 6

    def __init__(self, parent, command, bg=None, **kw):
        bg = bg or C['bg']
        super().__init__(parent, width=self.W, bg=bg,
                         highlightthickness=0, bd=0, **kw)
        self._command  = command
        self._y0       = 0.0
        self._y1       = 1.0
        self._dragging = False
        self._drag_y   = 0
        self._hovered  = False

        self.bind('<Configure>',       self._draw)
        self.bind('<ButtonPress-1>',   self._on_press)
        self.bind('<B1-Motion>',       self._on_drag)
        self.bind('<ButtonRelease-1>', self._on_release)
        self.bind('<Enter>',           self._on_enter)
        self.bind('<Leave>',           self._on_leave)

    def set(self, y0, y1):
        self._y0 = float(y0)
        self._y1 = float(y1)
        self._draw()

    def _thumb_coords(self):
        h = self.winfo_height() or 100
        return int(self._y0 * h), int(self._y1 * h)

    def _draw(self, e=None):
        self.delete('all')
        h = self.winfo_height() or 100
        w = self.winfo_width() or self.W
        self.create_rectangle(0, 0, w, h, fill=C['bg'], outline='')
        y0, y1 = self._thumb_coords()
        thumb_h = max(24, y1 - y0)
        y1 = min(y0 + thumb_h, h)
        pad = 1
        col = C['accent'] if self._hovered else C['surface3']
        x1, x2, r = pad, w - pad, (w - pad * 2) // 2
        if y1 - y0 >= 2 * r:
            self.create_oval(x1, y0, x2, y0+2*r, fill=col, outline='')
            self.create_rectangle(x1, y0+r, x2, y1-r, fill=col, outline='')
            self.create_oval(x1, y1-2*r, x2, y1, fill=col, outline='')
        else:
            self.create_oval(x1, y0, x2, y1, fill=col, outline='')

    def _on_enter(self, e):
        self._hovered = True; self._draw()

    def _on_leave(self, e):
        self._hovered = False; self._draw()

    def _on_press(self, e):
        y0, y1 = self._thumb_coords()
        if y0 <= e.y <= y1:
            self._dragging = True; self._drag_y = e.y - y0
        else:
            h = self.winfo_height() or 1
            frac = e.y / h
            self._command('moveto', str(frac - (self._y1 - self._y0) / 2))

    def _on_drag(self, e):
        if not self._dragging: return
        h = self.winfo_height() or 1
        self._command('moveto', str((e.y - self._drag_y) / h))

    def _on_release(self, e):
        self._dragging = False


class ScrollFrame(tk.Frame):
    """Frame scrollable avec scrollbar custom ultra-fine pill arrondie."""
    _active_canvas = None

    def __init__(self, parent, bg=None, **kw):
        bg = bg or C['bg']
        super().__init__(parent, bg=bg, **kw)

        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self._sb = CustomScrollbar(self, command=self._canvas.yview, bg=bg)
        self._canvas.configure(yscrollcommand=self._sb.set)

        self._sb.pack(side='right', fill='y', pady=4)
        self._canvas.pack(side='left', fill='both', expand=True)

        self.inner = tk.Frame(self._canvas, bg=bg)
        self._win  = self._canvas.create_window((0, 0), window=self.inner, anchor='nw')

        self.inner.bind('<Configure>', self._update_scroll)
        self._canvas.bind('<Configure>', self._on_resize)

        for w in (self._canvas, self.inner):
            w.bind('<Enter>', self._enter)
            w.bind('<Leave>', self._leave)

        self.bind_all('<MouseWheel>', self._wheel)
        self.bind_all('<Button-4>',   self._wheel_up_lx)
        self.bind_all('<Button-5>',   self._wheel_dn_lx)

    def _update_scroll(self, e=None):
        self._canvas.configure(scrollregion=self._canvas.bbox('all'))

    def _on_resize(self, e):
        self._canvas.itemconfig(self._win, width=e.width)

    def _enter(self, e=None):
        ScrollFrame._active_canvas = self._canvas

    def _leave(self, e=None):
        if ScrollFrame._active_canvas is self._canvas:
            ScrollFrame._active_canvas = None

    def _wheel(self, e):
        if ScrollFrame._active_canvas is not self._canvas: return
        steps = int(-1 * (e.delta / 120)) or (-1 if e.delta > 0 else 1)
        self._canvas.yview_scroll(steps, 'units')

    def _wheel_up_lx(self, e):
        if ScrollFrame._active_canvas is self._canvas:
            self._canvas.yview_scroll(-1, 'units')

    def _wheel_dn_lx(self, e):
        if ScrollFrame._active_canvas is self._canvas:
            self._canvas.yview_scroll(1, 'units')

    def scroll_to_top(self):
        self._canvas.yview_moveto(0)

    def bind_child_scroll(self, widget):
        widget.bind('<Enter>', self._enter)
        widget.bind('<Leave>', self._leave)


def scrollable_page(parent, bg=None):
    sf = ScrollFrame(parent, bg=bg)
    return sf, sf.inner


def make_tree_sb(parent, command):
    """Scrollbar custom fine pour Treeview."""
    return CustomScrollbar(parent, command=command, bg=C['surface'])


def pill_bar(parent, valeur, objectif, couleur, height=8, width=None):
    """Barre de progression pill-shaped arrondie."""
    pct = min(valeur / objectif, 1.0) if objectif > 0 else 0
    cv = tk.Canvas(parent, height=height, bg=C['surface2'],
                   highlightthickness=0)
    if width:
        cv.configure(width=width)
    r = height // 2

    def _draw(e=None):
        cv.delete('all')
        w = cv.winfo_width() or (width or 200)
        h = cv.winfo_height() or height
        # Fond pill
        rounded_rect(cv, 0, 0, w, h, r=r, fill=C['surface3'], outline='')
        # Remplissage
        fill_w = max(h, int(w * pct))
        if fill_w > 0:
            col = couleur if pct <= 1.0 else C['danger']
            rounded_rect(cv, 0, 0, fill_w, h, r=r, fill=col, outline='')

    cv.bind('<Configure>', _draw)
    return cv


class NutriApp(tk.Tk):
    """Fenêtre principale de l'application NutriTracker"""

    def __init__(self):
        super().__init__()
        self.title("NutriTracker — Suivi Nutritionnel")
        self.geometry("1280x820")
        self.minsize(1100, 700)
        self.configure(bg=C['bg'])

        # État courant
        self.date_courante = date.today()
        self.page_active = tk.StringVar(value='journal')
        self.entrees_du_jour: list[EntreeJournal] = []
        self.objectifs = charger_objectifs()
        self.profil = charger_profil()

        self._configurer_styles()
        self._construire_interface()
        self._charger_journal()
        self._bind_raccourcis()

    # ── RACCOURCIS CLAVIER ────────────────────────────────────────────────────
    def _bind_raccourcis(self):
        self.bind('<Left>',      lambda e: self._jour_precedent())
        self.bind('<Right>',     lambda e: self._jour_suivant())
        self.bind('<Control-n>', lambda e: self._ouvrir_dialog_ajout())
        self.bind('<Control-t>', lambda e: self._aller_aujourdhui())
        self.bind('<Control-a>', lambda e: self._afficher_page('aliments'))
        self.bind('<Control-j>', lambda e: self._afficher_page('journal'))
        self.bind('<Control-g>', lambda e: self._afficher_page('graphiques'))
        self.bind('<F5>',        lambda e: self._charger_journal())


    # ── STYLES TTK ────────────────────────────────────────────────────────────
    def _configurer_styles(self):
        style = ttk.Style(self)
        style.theme_use('clam')

        style.configure('.', background=C['bg'], foreground=C['text'],
                        font=FONT_BODY, borderwidth=0)
        style.configure('TFrame', background=C['bg'])

        # Labels
        style.configure('TLabel', background=C['bg'], foreground=C['text'], font=FONT_BODY)
        style.configure('Muted.TLabel', background=C['bg'], foreground=C['text_muted'], font=FONT_SMALL)

        # Boutons principaux
        style.configure('Accent.TButton', background=C['accent'], foreground='white',
                        font=FONT_BOLD, padding=(16, 9), relief='flat', borderwidth=0)
        style.map('Accent.TButton',
            background=[('active', C['accent_dim']), ('pressed', '#2d2870')])

        style.configure('Ghost.TButton', background=C['surface3'], foreground=C['text_muted'],
                        font=FONT_BODY, padding=(12, 7), relief='flat', borderwidth=0)
        style.map('Ghost.TButton',
            background=[('active', C['hover'])],
            foreground=[('active', C['text'])])

        style.configure('Teal.TButton', background=C['accent2'], foreground='#0a0a0f',
                        font=FONT_BOLD, padding=(14, 8), relief='flat', borderwidth=0)
        style.map('Teal.TButton', background=[('active', '#00a87e')])

        # Entries
        style.configure('TEntry', fieldbackground=C['surface3'], foreground=C['text'],
                        insertcolor=C['accent'], borderwidth=1, relief='flat',
                        selectbackground=C['accent'], selectforeground='white')
        style.configure('TCombobox', fieldbackground=C['surface3'], foreground=C['text'],
                        selectbackground=C['accent'], background=C['surface2'],
                        arrowcolor=C['text_muted'], borderwidth=0)
        style.map('TCombobox', fieldbackground=[('readonly', C['surface3'])],
                  foreground=[('readonly', C['text'])])

        # Treeview
        style.configure('Treeview', background=C['surface'], fieldbackground=C['surface'],
                        foreground=C['text'], font=FONT_BODY, rowheight=44, borderwidth=0)
        style.configure('Treeview.Heading', background=C['surface2'],
                        foreground=C['text_muted'], font=('Segoe UI', 10, 'bold'),
                        relief='flat', padding=(10, 8))
        style.map('Treeview',
            background=[('selected', C['surface3'])],
            foreground=[('selected', 'white')])
        style.map('Treeview.Heading', background=[('active', C['surface3'])])

        # Scrollbar fine et discrète
        style.configure('Thin.Vertical.TScrollbar', background=C['surface3'],
                        troughcolor=C['bg'], borderwidth=0, arrowsize=0,
                        width=6, arrowcolor=C['surface3'])
        style.configure('Vertical.TScrollbar', background=C['surface3'],
                        troughcolor=C['bg'], borderwidth=0, width=6,
                        arrowcolor=C['surface3'])
        style.map('Vertical.TScrollbar', background=[('active', C['text_muted'])])

        # Notebook tabs
        style.configure('TNotebook', background=C['bg'], borderwidth=0, tabmargins=0)
        style.configure('TNotebook.Tab', background=C['surface2'], foreground=C['text_muted'],
                        padding=(18, 9), font=FONT_BODY, borderwidth=0)
        style.map('TNotebook.Tab',
            background=[('selected', C['accent']), ('active', C['surface3'])],
            foreground=[('selected', 'white'), ('active', C['text'])])

    # ── CONSTRUCTION INTERFACE ────────────────────────────────────────────────
    def _construire_interface(self):
        # Conteneur principal
        self.main_container = tk.Frame(self, bg=C['bg'])
        self.main_container.pack(fill='both', expand=True)

        # Menu latéral
        self._creer_sidebar()

        # Zone de contenu
        self.content_frame = tk.Frame(self.main_container, bg=C['bg'])
        self.content_frame.pack(side='left', fill='both', expand=True)

        # Pages
        self.pages = {}
        self._creer_page_journal()
        self._creer_page_aliments()
        self._creer_page_objectifs()
        self._creer_page_graphiques()
        self._creer_page_sante()
        self._creer_page_stats()
        self._creer_page_profil()
        self._creer_page_complements()
        self._creer_page_supplements()

        self._afficher_page('journal')

    def _creer_sidebar(self):
        """Sidebar moderne avec items Canvas arrondis et indicateur actif."""
        SB_BG  = '#0f0f16'   # fond sidebar légèrement plus sombre
        SB_W   = 230
        sidebar = tk.Frame(self.main_container, bg=SB_BG, width=SB_W)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)

        # ── Logo ──────────────────────────────────────────────────────────────
        logo_cv = tk.Canvas(sidebar, height=72, bg=SB_BG, highlightthickness=0)
        logo_cv.pack(fill='x')

        def _draw_logo(e=None):
            logo_cv.delete('all')
            w = logo_cv.winfo_width() or SB_W
            # Dégradé accent sous forme de pill en haut
            logo_cv.create_text(w//2, 28, text='🥗 NutriTracker',
                                fill=C['text'], font=('Segoe UI', 13, 'bold'), anchor='center')
            logo_cv.create_text(w//2, 50, text='Suivi nutritionnel',
                                fill=C['text_muted'], font=FONT_SMALL, anchor='center')
        logo_cv.bind('<Configure>', _draw_logo)
        self.after(50, _draw_logo)

        # Séparateur lumineux
        sep_cv = tk.Canvas(sidebar, height=1, bg=SB_BG, highlightthickness=0)
        sep_cv.pack(fill='x', padx=20, pady=(0, 8))
        def _draw_sep(e=None):
            sep_cv.delete('all')
            w = sep_cv.winfo_width() or SB_W
            sep_cv.create_line(0, 0, w, 0, fill=C['border'])
        sep_cv.bind('<Configure>', _draw_sep)

        # ── Navigation items ──────────────────────────────────────────────────
        menu_items = [
            ('journal',      '📅', 'Journal'),
            ('aliments',     '🔍', 'Aliments'),
            ('objectifs',    '🎯', 'Objectifs'),
            ('graphiques',   '📈', 'Graphiques'),
            ('sante',        '🏥', 'Santé & Forme'),
            ('stats',        '📊', 'Statistiques'),
            ('profil',       '👤', 'Profil'),
            ('complements',  '💊', 'Compléments'),
            ('supplements',  '🧪', 'Suppléments'),
        ]

        self.btn_menu   = {}
        self._nav_items = {}   # page_id -> (canvas, icone, label)

        for page_id, icone, label in menu_items:
            cv = tk.Canvas(sidebar, height=40, bg=SB_BG, highlightthickness=0,
                           cursor='hand2')
            cv.pack(fill='x', padx=10, pady=2)

            def _make_draw(cv=cv, icone=icone, label=label, pid=page_id):
                def _draw(active=False, hovered=False, e=None):
                    cv.delete('all')
                    w = cv.winfo_width() or (SB_W - 20)
                    h = cv.winfo_height() or 40
                    r = 8
                    if active:
                        # Fond accent arrondi
                        pts = [r,0, w-r,0, w,0, w,r, w,h-r, w,h, w-r,h, r,h, 0,h, 0,h-r, 0,r, 0,0]
                        cv.create_polygon(pts, smooth=True,
                                          fill=C['accent'], outline='')
                        # Petit trait gauche lumineux
                        cv.create_rectangle(0, r, 3, h-r, fill='#a89fff', outline='')
                        fg = 'white'
                    elif hovered:
                        pts = [r,0, w-r,0, w,0, w,r, w,h-r, w,h, w-r,h, r,h, 0,h, 0,h-r, 0,r, 0,0]
                        cv.create_polygon(pts, smooth=True,
                                          fill=C['hover'], outline='')
                        fg = C['text']
                    else:
                        fg = C['text_muted']
                    cv.create_text(14, h//2, text=icone,
                                   fill=fg, font=('Segoe UI', 12), anchor='w')
                    cv.create_text(38, h//2, text=label,
                                   fill=fg, font=FONT_BODY, anchor='w')
                return _draw

            draw_fn = _make_draw()
            draw_fn(active=False, hovered=False)

            # Hover
            cv.bind('<Enter>',  lambda e, d=draw_fn, pid=page_id:
                                d(active=(self.page_active.get()==pid), hovered=True))
            cv.bind('<Leave>',  lambda e, d=draw_fn, pid=page_id:
                                d(active=(self.page_active.get()==pid), hovered=False))
            cv.bind('<Button-1>', lambda e, p=page_id: self._afficher_page(p))
            cv.bind('<Configure>', lambda e, d=draw_fn, pid=page_id:
                                   d(active=(self.page_active.get()==pid)))

            self.btn_menu[page_id]   = cv
            self._nav_items[page_id] = draw_fn

        # ── Bas sidebar : version + poids ─────────────────────────────────────
        bottom = tk.Frame(sidebar, bg=SB_BG)
        bottom.pack(side='bottom', fill='x', padx=16, pady=14)

        # Séparateur bas
        tk.Frame(bottom, height=1, bg=C['border']).pack(fill='x', pady=(0, 10))

        tk.Label(bottom, text='v1.0 · Open Source · Gratuit',
                 bg=SB_BG, fg=C['text_dim'],
                 font=('Segoe UI', 8)).pack(anchor='w')

    def _afficher_page(self, page_id: str):
        # Masquer toutes les pages
        for frame in self.pages.values():
            frame.pack_forget()

        # Redessiner tous les items nav
        self.page_active.set(page_id)
        for pid, draw_fn in self._nav_items.items():
            draw_fn(active=(pid == page_id), hovered=False)

        # Afficher la page demandée
        self.pages[page_id].pack(fill='both', expand=True)

        # Rafraîchir si besoin
        if page_id == 'journal':
            self._charger_journal()
        elif page_id == 'stats':
            self._rafraichir_stats()
        elif page_id == 'objectifs':
            self._rafraichir_objectifs()
        elif page_id == 'supplements':
            self._rafraichir_supplements()
        elif page_id == 'graphiques':
            self._page_graphiques.actualiser()
        elif page_id == 'sante':
            self._page_sante.actualiser()

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE JOURNAL
    # ═════════════════════════════════════════════════════════════════════════
    def _creer_page_journal(self):
        page = tk.Frame(self.content_frame, bg=C['bg'])
        self.pages['journal'] = page

        # ── En-tête fixe ──────────────────────────────────────────────────────
        header = tk.Frame(page, bg=C['bg'], pady=24)
        header.pack(fill='x', padx=40)

        nav_frame = tk.Frame(header, bg=C['bg'])
        nav_frame.pack(side='left')

        tk.Button(nav_frame, text="◀", bg=C['surface2'], fg=C['text'],
                  font=FONT_BOLD, relief='flat', cursor='hand2', padx=14, pady=8,
                  activebackground=C['hover'],
                  command=self._jour_precedent).pack(side='left', padx=(0, 6))

        self.lbl_date = tk.Label(nav_frame, text="",
                                  bg=C['bg'], fg=C['text'], font=FONT_TITLE)
        self.lbl_date.pack(side='left', padx=16)

        tk.Button(nav_frame, text="▶", bg=C['surface2'], fg=C['text'],
                  font=FONT_BOLD, relief='flat', cursor='hand2', padx=14, pady=8,
                  activebackground=C['hover'],
                  command=self._jour_suivant).pack(side='left', padx=(6, 0))

        tk.Button(nav_frame, text="Aujourd'hui", bg=C['surface3'], fg=C['text'],
                  font=FONT_BODY, relief='flat', cursor='hand2', padx=14, pady=8,
                  activebackground=C['hover'],
                  command=self._aller_aujourdhui).pack(side='left', padx=18)

        tk.Button(header, text="＋  Ajouter un aliment",
                  bg=C['accent'], fg='white', font=FONT_BOLD,
                  relief='flat', cursor='hand2', padx=20, pady=10,
                  activebackground=C['accent_dim'],
                  command=self._ouvrir_dialog_ajout).pack(side='right')

        # ── Zone haute scrollable (macros + barres) ───────────────────────────
        sf_top = ScrollFrame(page)
        sf_top.pack(fill='x', padx=40, pady=(0, 12))
        sf_top.configure(height=260)   # hauteur fixe — scroll si petit écran
        top_inner = sf_top.inner
        top_inner.configure(padx=0, pady=0)

        self.frame_macros = tk.Frame(top_inner, bg=C['bg'])
        self.frame_macros.pack(fill='x', pady=(6, 12))
        self._creer_cartes_macros()

        self.frame_progress = tk.Frame(top_inner, bg=C['surface2'], padx=24, pady=20)
        self.frame_progress.pack(fill='x', pady=(0, 8))
        self._creer_barres_progression()

        # ── Tableau journal (expand) ───────────────────────────────────────────
        journal_frame = tk.Frame(page, bg=C['surface'])
        journal_frame.pack(fill='both', expand=True, padx=40, pady=(0, 24))

        header_table = tk.Frame(journal_frame, bg=C['surface2'], pady=14)
        header_table.pack(fill='x')
        tk.Label(header_table, text="Journal alimentaire",
                 bg=C['surface2'], fg=C['text'], font=FONT_H2).pack(side='left', padx=20)
        tk.Button(header_table, text="🔍 Analyser la journée",
                  bg=C['surface3'], fg=C['text'], font=FONT_SMALL,
                  relief='flat', cursor='hand2', padx=14, pady=6,
                  activebackground=C['hover'],
                  command=self._analyser_journee).pack(side='right', padx=20)

        cols = ('repas', 'aliment', 'quantite', 'cal', 'prot', 'gluc', 'lip', 'fibres')
        self.tree_journal = ttk.Treeview(journal_frame, columns=cols,
                                          show='headings', selectmode='browse')
        for col, label, w in [
            ('repas', 'Repas', 90), ('aliment', 'Aliment', 250),
            ('quantite', 'Quantite', 80), ('cal', 'Kcal', 65),
            ('prot', 'Prot.', 65), ('gluc', 'Gluc.', 65),
            ('lip', 'Lip.', 65), ('fibres', 'Fibres', 65),
        ]:
            self.tree_journal.heading(col, text=label)
            self.tree_journal.column(col, width=w, anchor='center')
        self.tree_journal.column('aliment', anchor='w')

        scrollbar = make_tree_sb(journal_frame, command=self.tree_journal.yview)
        self.tree_journal.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.tree_journal.pack(fill='both', expand=True)

        # Scroll souris sur le treeview journal
        def _wheel_journal(e):
            self.tree_journal.yview_scroll(int(-1*(e.delta/120)), 'units')
        self.tree_journal.bind('<MouseWheel>', _wheel_journal)

        self.tree_journal.tag_configure('petit_dej', foreground='#fbbf24')
        self.tree_journal.tag_configure('dejeuner',  foreground='#4ade80')
        self.tree_journal.tag_configure('diner',     foreground='#38bdf8')
        self.tree_journal.tag_configure('collation', foreground='#fb923c')
        self.tree_journal.tag_configure('separator',
            background=C['surface2'], foreground=C['text_muted'],
            font=('Segoe UI', 9, 'bold'))

        actions_bar = tk.Frame(journal_frame, bg=C['surface2'], pady=7)
        actions_bar.pack(fill='x')
        for label, cmd in [
            ("✏️ Modifier", self._modifier_entree),
            ("🗑️ Supprimer", self._supprimer_entree),
            ("📋 Dupliquer", self._dupliquer_entree),
        ]:
            tk.Button(actions_bar, text=label,
                      bg=C['surface3'], fg=C['text_muted'],
                      font=FONT_SMALL, relief='flat', cursor='hand2',
                      padx=12, pady=5, activebackground=C['hover'],
                      activeforeground=C['text'],
                      command=cmd).pack(side='left', padx=5)

        self.frame_total = tk.Frame(journal_frame, bg=C['surface2'], pady=9)
        self.frame_total.pack(fill='x')
        self.lbl_total = tk.Label(self.frame_total,
                                   text="TOTAL : 0 kcal",
                                   bg=C['surface2'], fg=C['accent'], font=FONT_BOLD)
        self.lbl_total.pack(padx=16, side='left')

    def _creer_cartes_macros(self):
        """Cartes macros avec Canvas arrondi, bordure top colorée, mini pill bar."""
        for w in self.frame_macros.winfo_children():
            w.destroy()

        macros_def = [
            ('calories',  '🔥', 'Calories',  'kcal', C['cal']),
            ('proteines', '💪', 'Protéines', 'g',    C['prot']),
            ('glucides',  '🌾', 'Glucides',  'g',    C['gluc']),
            ('lipides',   '🫒', 'Lipides',   'g',    C['lip']),
            ('fibres',    '🌿', 'Fibres',    'g',    C['fibres']),
        ]

        self.cartes_labels = {}
        totaux = calculer_totaux(self.entrees_du_jour)
        obj = self.objectifs

        for i, (cle, icone, titre, unite, couleur) in enumerate(macros_def):
            # Canvas principal de la carte
            cv_card = tk.Canvas(self.frame_macros, bg=C['bg'],
                                highlightthickness=0, height=110)
            cv_card.grid(row=0, column=i, padx=8, pady=6, sticky='nsew')
            self.frame_macros.columnconfigure(i, weight=1)

            # Frame interne pour les widgets label
            inner = tk.Frame(cv_card, bg=C['surface2'])
            inner.pack(fill='both', expand=True, padx=0, pady=0)

            def _draw_card(e=None, cv=cv_card, col=couleur):
                cv.delete('bg_rect')
                w2, h2 = cv.winfo_width(), cv.winfo_height()
                if w2 < 4: return
                # Fond arrondi
                rounded_rect(cv, 0, 0, w2, h2, r=12,
                             fill=C['surface2'], outline=C['border'], width=1,
                             tags='bg_rect')
                # Bordure top colorée un peu plus épaisse
                cv.create_rectangle(3, 0, w2-3, 4, fill=col, outline='', tags='bg_rect')
                cv.lower('bg_rect')
            cv_card.bind('<Configure>', _draw_card)

            # Icone + titre
            top_row = tk.Frame(inner, bg=C['surface2'])
            top_row.pack(fill='x', padx=16, pady=(14, 4))
            tk.Label(top_row, text=icone, bg=C['surface2'],
                     fg=couleur, font=('Segoe UI', 12)).pack(side='left')
            tk.Label(top_row, text=f' {titre}', bg=C['surface2'],
                     fg=C['text_muted'], font=FONT_BODY).pack(side='left')

            valeur  = getattr(totaux, cle, 0)
            objectif = obj.get(cle, 0)
            texte_val = f"{valeur:.0f}" if cle == 'calories' else f"{valeur:.1f}"

            lbl_val = tk.Label(inner, text=f"{texte_val}",
                               bg=C['surface2'], fg=C['text'],
                               font=('Segoe UI', 18, 'bold'))
            lbl_val.pack(anchor='w', padx=16)

            lbl_obj = tk.Label(inner, text=f"/ {objectif} {unite}",
                               bg=C['surface2'], fg=C['text_muted'], font=FONT_SMALL)
            lbl_obj.pack(anchor='w', padx=16)

            # Mini pill bar
            cv_bar = tk.Canvas(inner, height=6, bg=C['surface2'], highlightthickness=0)
            cv_bar.pack(fill='x', padx=16, pady=(6, 14))

            def _draw_bar(e=None, cv=cv_bar, val=valeur, obj_=objectif, col=couleur):
                cv.delete('all')
                w_ = cv.winfo_width() or 120
                pct_ = min(val / obj_, 1.0) if obj_ > 0 else 0
                r_ = 3
                rounded_rect(cv, 0, 0, w_, 6, r=r_, fill=C['surface3'], outline='')
                fill_w = max(0, int(w_ * pct_))
                if fill_w > 0:
                    c_ = col if pct_ <= 1.0 else C['danger']
                    rounded_rect(cv, 0, 0, fill_w, 6, r=r_, fill=c_, outline='')
            cv_bar.bind('<Configure>', _draw_bar)

            self.cartes_labels[cle] = (lbl_val, lbl_obj, cv_bar, couleur, unite)

    def _creer_barres_progression(self):
        """Barres de progression pill arrondies style site web."""
        for w in self.frame_progress.winfo_children():
            w.destroy()

        tk.Label(self.frame_progress, text="Progression journalière",
                 bg=C['surface2'], fg=C['text'], font=FONT_H2
                 ).pack(anchor='w', pady=(0, 12))

        macros_barres = [
            ('calories',  '🔥 Calories',   C['cal'],      'kcal'),
            ('proteines', '💪 Protéines',  C['prot'],     'g'),
            ('glucides',  '🌾 Glucides',   C['gluc'],     'g'),
            ('lipides',   '🫒 Lipides',    C['lip'],      'g'),
            ('sucres',    '🍬 Sucres',     C['sucres_c'], 'g'),
            ('sel',       '🧂 Sel',        C['sel_c'],    'g'),
        ]

        self.barres = {}
        totaux = calculer_totaux(self.entrees_du_jour)

        for cle, label, couleur, unite in macros_barres:
            row = tk.Frame(self.frame_progress, bg=C['surface2'])
            row.pack(fill='x', pady=4)

            # Label + valeurs sur une ligne
            top = tk.Frame(row, bg=C['surface2'])
            top.pack(fill='x')
            tk.Label(top, text=label, bg=C['surface2'],
                     fg=C['text'], font=FONT_SMALL, width=16, anchor='w').pack(side='left')
            lbl_pct = tk.Label(top, text='', bg=C['surface2'],
                               fg=C['text_muted'], font=FONT_SMALL)
            lbl_pct.pack(side='right')

            # Pill bar canvas
            cv = tk.Canvas(row, height=7, bg=C['surface2'], highlightthickness=0)
            cv.pack(fill='x', pady=(3, 0))

            valeur   = getattr(totaux, cle, 0)
            objectif = self.objectifs.get(cle, 1)

            def _draw_pill(e=None, cv_=cv, val=valeur, obj_=objectif, col=couleur):
                cv_.delete('all')
                w_ = cv_.winfo_width() or 300
                pct_ = min(val / obj_, 1.0) if obj_ > 0 else 0
                r_ = 3
                # Fond
                rounded_rect(cv_, 0, 0, w_, 7, r=r_, fill=C['surface3'], outline='')
                # Fill
                fill_w = max(0, int(w_ * pct_))
                if fill_w > 0:
                    c_ = col if pct_ <= 1.0 else C['danger']
                    rounded_rect(cv_, 0, 0, fill_w, 7, r=r_, fill=c_, outline='')
            cv.bind('<Configure>', _draw_pill)

            self.barres[cle] = (cv, lbl_pct, couleur, unite)

        self._rafraichir_barres()

    def _rafraichir_barres(self):
        """Actualise les pill bars."""
        totaux = calculer_totaux(self.entrees_du_jour)
        self.update_idletasks()

        for cle, (cv, lbl_pct, couleur, unite) in self.barres.items():
            valeur   = getattr(totaux, cle, 0)
            objectif = self.objectifs.get(cle, 1)
            pct      = min(valeur / objectif, 1.0) if objectif > 0 else 0
            pct_txt  = int((valeur / objectif * 100)) if objectif > 0 else 0
            col_pct  = C['success'] if 80<=pct_txt<=115 else (C['danger'] if pct_txt>115 else C['text_muted'])
            lbl_pct.configure(
                text=f"{valeur:.0f} / {objectif} {unite}  {pct_txt}%",
                fg=col_pct,
            )
            w_ = cv.winfo_width() or 300
            cv.delete('all')
            r_ = 3
            rounded_rect(cv, 0, 0, w_, 7, r=r_, fill=C['surface3'], outline='')
            fill_w = max(0, int(w_ * pct))
            if fill_w > 0:
                c_ = couleur if pct <= 1.0 else C['danger']
                rounded_rect(cv, 0, 0, fill_w, 7, r=r_, fill=c_, outline='')

    def _actualiser_cartes(self):
        """Actualise les cartes macros."""
        totaux = calculer_totaux(self.entrees_du_jour)
        obj    = self.objectifs

        for cle, (lbl_val, lbl_obj, cv_bar, couleur, unite) in self.cartes_labels.items():
            valeur   = getattr(totaux, cle, 0)
            objectif = obj.get(cle, 0)
            texte    = f"{valeur:.0f}" if cle == 'calories' else f"{valeur:.1f}"
            lbl_val.configure(text=texte)
            lbl_obj.configure(text=f"/ {objectif} {unite}")

            self.update_idletasks()
            w_  = cv_bar.winfo_width() or 120
            pct = min(valeur / objectif, 1.0) if objectif > 0 else 0
            cv_bar.delete('all')
            rounded_rect(cv_bar, 0, 0, w_, 5, r=2, fill=C['surface3'], outline='')
            fw = max(0, int(w_ * pct))
            if fw > 0:
                c_ = couleur if pct <= 1.0 else C['danger']
                rounded_rect(cv_bar, 0, 0, fw, 5, r=2, fill=c_, outline='')

    def _charger_journal(self):
        """Charge et affiche le journal du jour"""
        self.entrees_du_jour = charger_journal(self.date_courante)
        self.objectifs = charger_objectifs()

        # Mise à jour de la date
        if self.date_courante == date.today():
            date_str = "Aujourd'hui"
        elif self.date_courante == date.today() - timedelta(days=1):
            date_str = "Hier"
        else:
            jours_fr = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
            mois_fr = ['jan.', 'fév.', 'mar.', 'avr.', 'mai', 'juin',
                       'juil.', 'août', 'sep.', 'oct.', 'nov.', 'déc.']
            j = self.date_courante
            date_str = f"{jours_fr[j.weekday()].capitalize()} {j.day} {mois_fr[j.month-1]}"
        self.lbl_date.configure(text=date_str)

        # Effacer le treeview
        self.tree_journal.delete(*self.tree_journal.get_children())

        # Remplir par repas
        repas_order = ['Petit-déjeuner', 'Déjeuner', 'Dîner', 'Collation']
        tags_repas = {
            'Petit-déjeuner': 'petit_dej',
            'Déjeuner': 'dejeuner',
            'Dîner': 'diner',
            'Collation': 'collation',
        }

        for repas in repas_order:
            entrees_repas = [e for e in self.entrees_du_jour
                             if e.repas.lower() == repas.lower()]
            if entrees_repas:
                # Séparateur de repas
                self.tree_journal.insert('', 'end',
                    values=(f"── {repas} ──", '', '', '', '', '', '', ''),
                    tags=('separator', tags_repas.get(repas, ''))
                )
                for e in entrees_repas:
                    v = e.valeurs_calculees
                    self.tree_journal.insert('', 'end',
                        iid=e.id_entree,
                        values=(
                            '',
                            e.aliment_nom,
                            f"{e.quantite_g:.0f} g",
                            f"{v.calories:.0f}",
                            f"{v.proteines:.1f}",
                            f"{v.glucides:.1f}",
                            f"{v.lipides:.1f}",
                            f"{v.fibres:.1f}",
                        ),
                        tags=(tags_repas.get(repas, ''),)
                    )

        # Style séparateurs
        self.tree_journal.tag_configure('separator',
            background=C['surface2'], foreground=C['text_muted'],
            font=('Segoe UI', 9, 'bold'))

        # Totaux
        totaux = calculer_totaux(self.entrees_du_jour)
        self.lbl_total.configure(
            text=f"TOTAL : {totaux.calories:.0f} kcal  |  "
                 f"{totaux.proteines:.1f}g prot.  |  "
                 f"{totaux.glucides:.1f}g gluc.  |  "
                 f"{totaux.lipides:.1f}g lip.  |  "
                 f"{totaux.fibres:.1f}g fibres  |  "
                 f"{totaux.sel:.2f}g sel"
        )

        # Actualiser macros
        if hasattr(self, 'cartes_labels'):
            self._actualiser_cartes()
        if hasattr(self, 'barres'):
            self._rafraichir_barres()

    def _jour_precedent(self):
        self.date_courante -= timedelta(days=1)
        self._charger_journal()

    def _jour_suivant(self):
        if self.date_courante < date.today():
            self.date_courante += timedelta(days=1)
            self._charger_journal()

    def _aller_aujourdhui(self):
        self.date_courante = date.today()
        self._charger_journal()

    # ── DIALOGS AJOUT / MODIFICATION ─────────────────────────────────────────
    def _ouvrir_dialog_ajout(self, aliment_prefill: Aliment = None):
        """Ouvre le dialogue d'ajout d'un aliment au journal"""
        dialog = DialogAjoutAliment(self, aliment_prefill)
        self.wait_window(dialog)
        if dialog.resultat:
            aliment, quantite, repas = dialog.resultat
            valeurs = aliment.valeurs_100g.calculer_pour_quantite(quantite)
            entree = EntreeJournal(
                aliment_id=aliment.id,
                aliment_nom=str(aliment),
                quantite_g=quantite,
                valeurs_calculees=valeurs,
                repas=repas,
                heure=datetime.now().strftime('%H:%M'),
            )
            ajouter_entree_journal(entree, self.date_courante)
            self._charger_journal()

    def _modifier_entree(self):
        """Modifie l'entrée sélectionnée"""
        selection = self.tree_journal.selection()
        if not selection:
            messagebox.showinfo("Info", "Sélectionnez une entrée à modifier")
            return
        id_entree = selection[0]
        entree = next((e for e in self.entrees_du_jour if e.id_entree == id_entree), None)
        if not entree:
            return

        dialog = DialogModifierEntree(self, entree)
        self.wait_window(dialog)
        if dialog.resultat:
            quantite, repas = dialog.resultat
            aliments = charger_aliments()
            aliment = next((a for a in aliments if a.id == entree.aliment_id), None)
            if aliment:
                entree.quantite_g = quantite
                entree.repas = repas
                entree.valeurs_calculees = aliment.valeurs_100g.calculer_pour_quantite(quantite)
                modifier_entree_journal(entree, self.date_courante)
                self._charger_journal()

    def _supprimer_entree(self):
        """Supprime l'entrée sélectionnée"""
        selection = self.tree_journal.selection()
        if not selection:
            messagebox.showinfo("Info", "Sélectionnez une entrée à supprimer")
            return
        id_entree = selection[0]
        entree = next((e for e in self.entrees_du_jour if e.id_entree == id_entree), None)
        if not entree:
            return
        if messagebox.askyesno("Confirmer", f"Supprimer '{entree.aliment_nom}' ?"):
            supprimer_entree_journal(id_entree, self.date_courante)
            self._charger_journal()

    def _dupliquer_entree(self):
        """Duplique l'entrée sélectionnée"""
        selection = self.tree_journal.selection()
        if not selection:
            return
        id_entree = selection[0]
        entree = next((e for e in self.entrees_du_jour if e.id_entree == id_entree), None)
        if entree:
            import uuid
            nouvelle = EntreeJournal(
                aliment_id=entree.aliment_id,
                aliment_nom=entree.aliment_nom,
                quantite_g=entree.quantite_g,
                valeurs_calculees=entree.valeurs_calculees,
                repas=entree.repas,
                heure=datetime.now().strftime('%H:%M'),
            )
            ajouter_entree_journal(nouvelle, self.date_courante)
            self._charger_journal()

    def _analyser_journee(self):
        """Analyse nutritionnelle de la journée"""
        if not self.entrees_du_jour:
            messagebox.showinfo("Analyse", "Aucune entrée dans le journal pour cette journée.")
            return
        conseils = analyser_journee(self.entrees_du_jour, self.objectifs)
        DialogAnalyseJournee(self, conseils)

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE ALIMENTS
    # ═════════════════════════════════════════════════════════════════════════
    def _creer_page_aliments(self):
        page = tk.Frame(self.content_frame, bg=C['bg'])
        self.pages['aliments'] = page

        # En-tête
        header = tk.Frame(page, bg=C['bg'], pady=20)
        header.pack(fill='x', padx=30)
        tk.Label(header, text="Base de données alimentaire",
                 bg=C['bg'], fg=C['text'], font=FONT_TITLE).pack(side='left')

        # Boutons actions
        btns_frame = tk.Frame(header, bg=C['bg'])
        btns_frame.pack(side='right')

        tk.Button(btns_frame, text="+ Nouvel aliment",
                  bg=C['accent'], fg='white', font=FONT_BOLD,
                  relief='flat', cursor='hand2', padx=14, pady=8,
                  activebackground='#c73652',
                  command=self._dialog_nouvel_aliment).pack(side='left', padx=5)

        # Barre de recherche
        search_frame = tk.Frame(page, bg=C['surface'], padx=15, pady=10)
        search_frame.pack(fill='x', padx=30, pady=(0, 10))

        tk.Label(search_frame, text="🔍", bg=C['surface'], fg=C['text_muted'],
                 font=('Segoe UI', 14)).pack(side='left')

        self.var_recherche = tk.StringVar()

        entry_search = tk.Entry(search_frame, textvariable=self.var_recherche,
                                bg=C['surface2'], fg=C['text'],
                                insertbackground=C['text'],
                                font=FONT_BODY, relief='flat', bd=5)
        entry_search.pack(side='left', fill='x', expand=True, padx=10)
        entry_search.insert(0, "Rechercher un aliment...")
        entry_search.bind('<FocusIn>', lambda e: entry_search.delete(0, 'end')
                           if entry_search.get() == "Rechercher un aliment..." else None)

        # Filtre catégorie
        self.var_categorie = tk.StringVar(value='Toutes')
        self.var_recherche.trace('w', self._filtrer_aliments)
        categories = ['Toutes', 'viandes', 'poissons', 'oeufs', 'feculents',
                      'legumes', 'fruits', 'laitiers', 'oleagineux',
                      'legumineuses', 'complements', 'boissons', 'autre']
        combo_cat = ttk.Combobox(search_frame, textvariable=self.var_categorie,
                                  values=categories, state='readonly', width=14)
        combo_cat.pack(side='right', padx=5)
        combo_cat.bind('<<ComboboxSelected>>', lambda e: self._filtrer_aliments())

        tk.Label(search_frame, text="Catégorie :",
                 bg=C['surface'], fg=C['text_muted'], font=FONT_SMALL).pack(side='right')

        # Treeview aliments
        aliments_frame = tk.Frame(page, bg=C['surface'])
        aliments_frame.pack(fill='both', expand=True, padx=30, pady=(0, 20))

        cols = ('nom', 'marque', 'categorie', 'cal', 'prot', 'gluc', 'lip', 'fibres', 'favori')
        self.tree_aliments = ttk.Treeview(aliments_frame, columns=cols,
                                           show='headings', selectmode='browse')

        for col, (label, width) in {
            'nom':       ('Aliment',     220),
            'marque':    ('Marque',      110),
            'categorie': ('Catégorie',   100),
            'cal':       ('Kcal/100g',    80),
            'prot':      ('Prot.',        70),
            'gluc':      ('Gluc.',        70),
            'lip':       ('Lip.',         70),
            'fibres':    ('Fibres',       70),
            'favori':    ('⭐',           40),
        }.items():
            self.tree_aliments.heading(col, text=label,
                command=lambda c=col: self._trier_aliments(c))
            self.tree_aliments.column(col, width=width, anchor='center')
        self.tree_aliments.column('nom', anchor='w')

        scroll_al = ttk.Scrollbar(aliments_frame, orient='vertical',
                                   command=self.tree_aliments.yview)
        self.tree_aliments.configure(yscrollcommand=scroll_al.set)
        scroll_al.pack(side='right', fill='y')
        self.tree_aliments.pack(fill='both', expand=True)

        # Scroll souris sur le treeview aliments
        def _wheel_aliments(e):
            self.tree_aliments.yview_scroll(int(-1*(e.delta/120)), 'units')
        self.tree_aliments.bind('<MouseWheel>', _wheel_aliments)

        # Double-clic pour ajouter au journal
        self.tree_aliments.bind('<Double-1>', self._ajouter_depuis_aliments)

        # Barre actions aliments
        act_bar = tk.Frame(aliments_frame, bg=C['surface2'], pady=8)
        act_bar.pack(fill='x')

        for label, cmd in [
            ("➕ Ajouter au journal", self._ajouter_depuis_aliments),
            ("✏️ Modifier",           self._modifier_aliment_db),
            ("⭐ Favori",             self._toggler_favori),
            ("🔍 Analyser",          self._analyser_aliment_selectionne),
            ("🗑️ Supprimer",         self._supprimer_aliment_db),
        ]:
            tk.Button(act_bar, text=label,
                      bg=C['surface'], fg=C['text_muted'],
                      font=FONT_SMALL, relief='flat', cursor='hand2',
                      padx=12, pady=5, activebackground=C['hover'],
                      activeforeground=C['text'],
                      command=cmd).pack(side='left', padx=5)

        self._tri_aliments = ('nom', False)
        self._charger_liste_aliments()

    def _charger_liste_aliments(self, aliments=None):
        """Remplit le treeview avec la liste des aliments"""
        self.tree_aliments.delete(*self.tree_aliments.get_children())
        if aliments is None:
            aliments = charger_aliments()
        for a in aliments:
            v = a.valeurs_100g
            self.tree_aliments.insert('', 'end', iid=a.id, values=(
                a.nom,
                a.marque,
                a.categorie,
                f"{v.calories:.0f}",
                f"{v.proteines:.1f}",
                f"{v.glucides:.1f}",
                f"{v.lipides:.1f}",
                f"{v.fibres:.1f}",
                '⭐' if a.favoris else '',
            ))

    def _filtrer_aliments(self, *args):
        """Filtre la liste en temps réel"""
        query = self.var_recherche.get().strip()
        if query == "Rechercher un aliment...":
            query = ""
        cat = self.var_categorie.get()
        aliments = rechercher_aliment(query)
        if cat != 'Toutes':
            aliments = [a for a in aliments if a.categorie == cat]
        self._charger_liste_aliments(aliments)

    def _trier_aliments(self, colonne: str):
        """Trie la liste par colonne"""
        col_actuelle, ordre_actuel = self._tri_aliments
        ordre = not ordre_actuel if col_actuelle == colonne else False
        self._tri_aliments = (colonne, ordre)
        aliments = charger_aliments()
        map_col = {
            'nom': lambda a: a.nom,
            'marque': lambda a: a.marque,
            'categorie': lambda a: a.categorie,
            'cal': lambda a: a.valeurs_100g.calories,
            'prot': lambda a: a.valeurs_100g.proteines,
            'gluc': lambda a: a.valeurs_100g.glucides,
            'lip': lambda a: a.valeurs_100g.lipides,
            'fibres': lambda a: a.valeurs_100g.fibres,
        }
        key = map_col.get(colonne, lambda a: a.nom)
        aliments.sort(key=key, reverse=ordre)
        self._charger_liste_aliments(aliments)

    def _ajouter_depuis_aliments(self, event=None):
        """Ajoute l'aliment sélectionné au journal"""
        selection = self.tree_aliments.selection()
        if not selection:
            return
        aliment_id = selection[0]
        aliments = charger_aliments()
        aliment = next((a for a in aliments if a.id == aliment_id), None)
        if aliment:
            self._ouvrir_dialog_ajout(aliment)

    def _modifier_aliment_db(self):
        """Ouvre le dialog de modification d'aliment"""
        selection = self.tree_aliments.selection()
        if not selection:
            messagebox.showinfo("Info", "Sélectionnez un aliment")
            return
        aliment_id = selection[0]
        aliments = charger_aliments()
        aliment = next((a for a in aliments if a.id == aliment_id), None)
        if aliment:
            dialog = DialogAlimentForm(self, aliment)
            self.wait_window(dialog)
            if dialog.resultat:
                from database.db_manager import modifier_aliment
                modifier_aliment(dialog.resultat)
                self._charger_liste_aliments()

    def _toggler_favori(self):
        selection = self.tree_aliments.selection()
        if not selection:
            return
        basculer_favori(selection[0])
        self._charger_liste_aliments()

    def _analyser_aliment_selectionne(self):
        selection = self.tree_aliments.selection()
        if not selection:
            return
        aliments = charger_aliments()
        aliment = next((a for a in aliments if a.id == selection[0]), None)
        if aliment:
            DialogAnalyseAliment(self, aliment, self.profil.objectif)

    def _supprimer_aliment_db(self):
        selection = self.tree_aliments.selection()
        if not selection:
            return
        if messagebox.askyesno("Supprimer", "Supprimer cet aliment de la base ?"):
            from database.db_manager import supprimer_aliment
            supprimer_aliment(selection[0])
            self._charger_liste_aliments()

    def _dialog_nouvel_aliment(self):
        dialog = DialogAlimentForm(self)
        self.wait_window(dialog)
        if dialog.resultat:
            from database.db_manager import ajouter_aliment
            ok = ajouter_aliment(dialog.resultat)
            if not ok:
                messagebox.showwarning("Doublon", "Un aliment avec ce nom existe déjà.")
            else:
                self._charger_liste_aliments()

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE GRAPHIQUES
    # ═════════════════════════════════════════════════════════════════════════
    def _creer_page_graphiques(self):
        from ui.graphiques import PageGraphiques
        page = tk.Frame(self.content_frame, bg=C['bg'])
        self.pages['graphiques'] = page
        self._page_graphiques = PageGraphiques(page)
        self._page_graphiques.pack(fill='both', expand=True)

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE SANTÉ
    # ═════════════════════════════════════════════════════════════════════════
    def _creer_page_sante(self):
        from ui.sante import PageSante
        page = tk.Frame(self.content_frame, bg=C['bg'])
        self.pages['sante'] = page
        self._page_sante = PageSante(page)
        self._page_sante.pack(fill='both', expand=True)

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE STATS
    # ═════════════════════════════════════════════════════════════════════════
    def _creer_page_stats(self):
        page = tk.Frame(self.content_frame, bg=C['bg'])
        self.pages['stats'] = page

        # En-tête fixe (hors scroll)
        tk.Label(page, text="📊 Statistiques",
                 bg=C['bg'], fg=C['text'], font=FONT_TITLE).pack(pady=20, padx=30, anchor='w')

        # ScrollFrame pour tout le contenu
        sf = ScrollFrame(page)
        sf.pack(fill='both', expand=True)
        self.frame_stats_content = sf.inner
        self.frame_stats_content.configure(padx=30, pady=10)

    def _rafraichir_stats(self):
        for w in self.frame_stats_content.winfo_children():
            w.destroy()

        dates = charger_dates_journal()
        if not dates:
            tk.Label(self.frame_stats_content,
                     text="Aucune donnée dans le journal.",
                     bg=C['bg'], fg=C['text_muted'], font=FONT_BODY).pack(pady=50)
            return

        # Statistiques des 7 derniers jours
        tk.Label(self.frame_stats_content,
                 text="Moyennes sur les 7 derniers jours",
                 bg=C['bg'], fg=C['text'], font=FONT_H2).pack(anchor='w', pady=(0, 15))

        from datetime import date as dt
        today = dt.today()
        totaux_semaine = []
        for i in range(7):
            d = today - timedelta(days=i)
            entrees = charger_journal(d)
            if entrees:
                totaux_semaine.append((d, calculer_totaux(entrees)))

        if totaux_semaine:
            n = len(totaux_semaine)
            moyennes = {
                'calories': sum(t.calories for _, t in totaux_semaine) / n,
                'proteines': sum(t.proteines for _, t in totaux_semaine) / n,
                'glucides': sum(t.glucides for _, t in totaux_semaine) / n,
                'lipides': sum(t.lipides for _, t in totaux_semaine) / n,
                'fibres': sum(t.fibres for _, t in totaux_semaine) / n,
            }
            obj = self.objectifs
            grid = tk.Frame(self.frame_stats_content, bg=C['bg'])
            grid.pack(fill='x')

            stats_items = [
                ('🔥 Calories',  'calories',  'kcal', C['cal']),
                ('💪 Protéines', 'proteines', 'g',    C['prot']),
                ('🌾 Glucides',  'glucides',  'g',    C['gluc']),
                ('🫒 Lipides',   'lipides',   'g',    C['lip']),
                ('🌿 Fibres',    'fibres',    'g',    C['fibres']),
            ]

            for i, (label, cle, unite, couleur) in enumerate(stats_items):
                card = tk.Frame(grid, bg=C['surface'], padx=20, pady=15)
                card.grid(row=0, column=i, padx=6, sticky='ew')
                grid.columnconfigure(i, weight=1)

                tk.Label(card, text=label, bg=C['surface'],
                         fg=C['text_muted'], font=FONT_SMALL).pack(anchor='w')
                moy = moyennes[cle]
                objectif = obj.get(cle, 1)
                pct = int(moy / objectif * 100) if objectif else 0
                tk.Label(card, text=f"{moy:.0f} {unite}",
                         bg=C['surface'], fg=couleur,
                         font=('Segoe UI', 18, 'bold')).pack(anchor='w')
                couleur_pct = C['success'] if 80 <= pct <= 115 else C['warning']
                tk.Label(card, text=f"{pct}% de l'objectif",
                         bg=C['surface'], fg=couleur_pct, font=FONT_SMALL).pack(anchor='w')

        # Historique
        tk.Label(self.frame_stats_content, text="Historique des journées",
                 bg=C['bg'], fg=C['text'], font=FONT_H2).pack(anchor='w', pady=(25, 10))

        hist_frame = tk.Frame(self.frame_stats_content, bg=C['surface'])
        hist_frame.pack(fill='both', expand=True)

        cols = ('date', 'kcal', 'prot', 'gluc', 'lip', 'fibres', 'sel')
        tree_hist = ttk.Treeview(hist_frame, columns=cols, show='headings', height=12)
        for col, label, w in [
            ('date', 'Date', 120), ('kcal', 'Kcal', 80),
            ('prot', 'Prot.', 80), ('gluc', 'Gluc.', 80),
            ('lip', 'Lip.', 80), ('fibres', 'Fibres', 80), ('sel', 'Sel', 80)
        ]:
            tree_hist.heading(col, text=label)
            tree_hist.column(col, width=w, anchor='center')

        for d_str in dates[:30]:
            try:
                d = date.fromisoformat(d_str)
            except Exception:
                continue
            entrees = charger_journal(d)
            if entrees:
                t = calculer_totaux(entrees)
                mois_fr = ['Jan.', 'Fév.', 'Mar.', 'Avr.', 'Mai', 'Juin',
                           'Juil.', 'Août', 'Sep.', 'Oct.', 'Nov.', 'Déc.']
                date_affichee = f"{d.day} {mois_fr[d.month-1]} {d.year}"
                tree_hist.insert('', 'end', values=(
                    date_affichee,
                    f"{t.calories:.0f}", f"{t.proteines:.1f}",
                    f"{t.glucides:.1f}", f"{t.lipides:.1f}",
                    f"{t.fibres:.1f}", f"{t.sel:.2f}",
                ))

        sc = ttk.Scrollbar(hist_frame, orient='vertical', command=tree_hist.yview)
        tree_hist.configure(yscrollcommand=sc.set)
        sc.pack(side='right', fill='y')
        tree_hist.pack(fill='both', expand=True)

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE PROFIL
    # ═════════════════════════════════════════════════════════════════════════
    def _creer_page_profil(self):
        page = tk.Frame(self.content_frame, bg=C['bg'])
        self.pages['profil'] = page

        # En-tête fixe
        tk.Label(page, text="👤 Profil & Objectifs",
                 bg=C['bg'], fg=C['text'], font=FONT_TITLE).pack(pady=20, padx=30, anchor='w')

        # ScrollFrame
        sf = ScrollFrame(page)
        sf.pack(fill='both', expand=True)
        scroll_inner = sf.inner
        scroll_inner.configure(padx=30, pady=5)

        # Formulaire profil
        form_outer = tk.Frame(scroll_inner, bg=C['surface2'], padx=30, pady=25)
        form_outer.pack(fill='x', pady=(0, 20))

        tk.Label(form_outer, text="Informations personnelles",
                 bg=C['surface2'], fg=C['text_muted'],
                 font=FONT_SMALL).grid(row=0, column=0, columnspan=2,
                                       sticky='w', pady=(0, 12))

        profil = charger_profil()

        champs = [
            ('Nom', 'nom', 'entry', profil.nom),
            ('Age', 'age', 'entry', str(profil.age)),
            ('Taille (cm)', 'taille_cm', 'entry', str(profil.taille_cm)),
            ('Poids (kg)', 'poids_kg', 'entry', str(profil.poids_kg)),
            ('Sexe', 'sexe', 'combo', ['homme', 'femme'], profil.sexe),
            ('Activite physique', 'activite', 'combo',
             ['sedentaire', 'legere', 'moderee', 'intense', 'tres_intense'],
             profil.activite),
            ('Objectif', 'objectif', 'combo',
             ['seche', 'maintien', 'prise_masse'],
             profil.objectif),
        ]

        self.vars_profil = {}
        for i, champ in enumerate(champs):
            nom_label, cle = champ[0], champ[1]
            type_widget = champ[2]
            row_i = i + 1

            tk.Label(form_outer, text=nom_label + " :",
                     bg=C['surface2'], fg=C['text'],
                     font=FONT_BODY).grid(
                row=row_i, column=0, sticky='w', pady=7, padx=(0, 20))

            if type_widget == 'entry':
                var = tk.StringVar(value=champ[3])
                tk.Entry(form_outer, textvariable=var,
                         bg=C['surface3'], fg=C['text'],
                         insertbackground=C['accent'],
                         font=FONT_BODY, relief='flat', bd=6, width=26).grid(
                    row=row_i, column=1, sticky='w', pady=7)
            else:
                var = tk.StringVar(value=champ[4])
                ttk.Combobox(form_outer, textvariable=var,
                             values=champ[3], state='readonly', width=23).grid(
                    row=row_i, column=1, sticky='w', pady=7)
            self.vars_profil[cle] = var

        # Bouton sauvegarde
        btn_frame = tk.Frame(scroll_inner, bg=C['bg'])
        btn_frame.pack(fill='x', pady=(0, 20))
        tk.Button(btn_frame,
                  text="💾  Sauvegarder et recalculer les objectifs",
                  bg=C['accent'], fg='white', font=FONT_BOLD,
                  relief='flat', cursor='hand2', padx=22, pady=11,
                  activebackground=C['accent_dim'],
                  command=self._sauvegarder_profil).pack(side='left')

        # Zone objectifs calculés
        self.frame_objectifs_affiches = tk.Frame(scroll_inner, bg=C['bg'])
        self.frame_objectifs_affiches.pack(fill='x', pady=(0, 30))
        self._afficher_objectifs_actuels()

    def _sauvegarder_profil(self):
        try:
            profil = ProfilUtilisateur(
                nom=self.vars_profil['nom'].get(),
                age=int(self.vars_profil['age'].get()),
                taille_cm=float(self.vars_profil['taille_cm'].get()),
                poids_kg=float(self.vars_profil['poids_kg'].get()),
                sexe=self.vars_profil['sexe'].get(),
                activite=self.vars_profil['activite'].get(),
                objectif=self.vars_profil['objectif'].get(),
            )
            from database.db_manager import sauvegarder_profil
            sauvegarder_profil(profil)
            self.profil = profil
            self.objectifs = charger_objectifs()
            self._afficher_objectifs_actuels()
            messagebox.showinfo("Succès", "Profil sauvegardé ! Les objectifs ont été recalculés.")
        except ValueError as e:
            messagebox.showerror("Erreur", f"Valeurs invalides : {e}")

    def _afficher_objectifs_actuels(self):
        for w in self.frame_objectifs_affiches.winfo_children():
            w.destroy()

        obj = charger_objectifs()
        profil = charger_profil()
        tdee = profil.calcul_tdee()

        tk.Label(self.frame_objectifs_affiches,
                 text=f"Objectifs journaliers — {profil.objectif.replace('_', ' ').title()}",
                 bg=C['surface'], fg=C['text'], font=FONT_H2).grid(
            row=0, column=0, columnspan=4, sticky='w', pady=(0, 15))

        tk.Label(self.frame_objectifs_affiches,
                 text=f"Métabolisme de base : {profil.calcul_bmr():.0f} kcal   |   "
                      f"TDEE : {tdee} kcal",
                 bg=C['surface'], fg=C['text_muted'], font=FONT_SMALL).grid(
            row=1, column=0, columnspan=4, sticky='w', pady=(0, 15))

        items = [
            ('🔥 Calories',  f"{obj.get('calories', 0)} kcal",  C['cal']),
            ('💪 Protéines', f"{obj.get('proteines', 0)} g",     C['prot']),
            ('🌾 Glucides',  f"{obj.get('glucides', 0)} g",      C['gluc']),
            ('🫒 Lipides',   f"{obj.get('lipides', 0)} g",       C['lip']),
            ('🌿 Fibres',    f"{obj.get('fibres', 0)} g",        C['fibres']),
            ('🧂 Sel',       f"{obj.get('sel', 0)} g",           C['text_muted']),
        ]
        for i, (label, valeur, couleur) in enumerate(items):
            col = i % 3
            row_base = 2 + (i // 3) * 2
            f = tk.Frame(self.frame_objectifs_affiches, bg=C['surface2'],
                         padx=15, pady=10)
            f.grid(row=row_base, column=col, padx=6, pady=4, sticky='ew')
            self.frame_objectifs_affiches.columnconfigure(col, weight=1)
            tk.Label(f, text=label, bg=C['surface2'],
                     fg=C['text_muted'], font=FONT_SMALL).pack(anchor='w')
            tk.Label(f, text=valeur, bg=C['surface2'],
                     fg=couleur, font=('Segoe UI', 16, 'bold')).pack(anchor='w')

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE COMPLÉMENTS
    # ═════════════════════════════════════════════════════════════════════════
    def _creer_page_complements(self):
        page = tk.Frame(self.content_frame, bg=C['bg'])
        self.pages['complements'] = page

        # En-tête fixe
        header = tk.Frame(page, bg=C['bg'], pady=20)
        header.pack(fill='x', padx=30)
        tk.Label(header, text="💊 Compléments alimentaires",
                 bg=C['bg'], fg=C['text'], font=FONT_TITLE).pack(side='left')
        tk.Button(header, text="+ Ajouter au journal",
                  bg=C['accent'], fg='white', font=FONT_BOLD,
                  relief='flat', cursor='hand2', padx=14, pady=8,
                  activebackground=C['accent_dim'],
                  command=self._filtrer_et_ajouter_complement).pack(side='right')

        # Info banner
        info = tk.Frame(page, bg=C['surface2'], padx=20, pady=12)
        info.pack(fill='x', padx=30, pady=(0, 12))
        tk.Label(info,
                 text="Double-cliquez sur un complément pour l'ajouter directement au journal.",
                 bg=C['surface2'], fg=C['text_muted'], font=FONT_BODY).pack(anchor='w')

        # Treeview avec sa propre scrollbar (toujours visible)
        comp_frame = tk.Frame(page, bg=C['surface'])
        comp_frame.pack(fill='both', expand=True, padx=30, pady=(0, 20))

        cols = ('nom', 'marque', 'cal', 'prot', 'gluc', 'lip')
        self.tree_comps = ttk.Treeview(comp_frame, columns=cols,
                                        show='headings', selectmode='browse')
        for col, label, w in [
            ('nom', 'Complement', 260), ('marque', 'Marque', 160),
            ('cal', 'Kcal/100g', 100), ('prot', 'Prot.', 90),
            ('gluc', 'Gluc.', 90), ('lip', 'Lip.', 90),
        ]:
            self.tree_comps.heading(col, text=label)
            self.tree_comps.column(col, width=w, anchor='center')
        self.tree_comps.column('nom', anchor='w')
        self.tree_comps.bind('<Double-1>', self._ajouter_complement_journal)

        sc = make_tree_sb(comp_frame, command=self.tree_comps.yview)
        self.tree_comps.configure(yscrollcommand=sc.set)
        sc.pack(side='right', fill='y')
        self.tree_comps.pack(fill='both', expand=True)

        # Scroll souris sur le treeview
        def _wheel_comp(e):
            self.tree_comps.yview_scroll(int(-1*(e.delta/120)), 'units')
        self.tree_comps.bind('<MouseWheel>', _wheel_comp)

        # Barre actions
        act_bar = tk.Frame(page, bg=C['surface2'], pady=8)
        act_bar.pack(fill='x', padx=30)
        tk.Button(act_bar, text="➕ Ajouter au journal",
                  bg=C['surface3'], fg=C['text'], font=FONT_SMALL,
                  relief='flat', cursor='hand2', padx=12, pady=6,
                  activebackground=C['hover'], activeforeground=C['text'],
                  command=self._filtrer_et_ajouter_complement).pack(side='left', padx=5)

        self._charger_complements()

    def _charger_complements(self):
        self.tree_comps.delete(*self.tree_comps.get_children())
        aliments = charger_aliments()
        for a in aliments:
            if a.categorie == 'complements':
                v = a.valeurs_100g
                self.tree_comps.insert('', 'end', iid=a.id, values=(
                    a.nom, a.marque,
                    f"{v.calories:.0f}", f"{v.proteines:.1f}",
                    f"{v.glucides:.1f}", f"{v.lipides:.1f}",
                ))

    def _ajouter_complement_journal(self, event=None):
        selection = self.tree_comps.selection()
        if not selection:
            return
        aliments = charger_aliments()
        aliment = next((a for a in aliments if a.id == selection[0]), None)
        if aliment:
            self._ouvrir_dialog_ajout(aliment)

    def _filtrer_et_ajouter_complement(self):
        selection = self.tree_comps.selection()
        if selection:
            self._ajouter_complement_journal()
        else:
            messagebox.showinfo("Info", "Sélectionnez un complément dans la liste, puis double-cliquez ou cliquez 'Ajouter'.")


# ═══════════════════════════════════════════════════════════════════════════════
# DIALOGUES
# ═══════════════════════════════════════════════════════════════════════════════

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE OBJECTIFS
    # ═════════════════════════════════════════════════════════════════════════
    def _creer_page_objectifs(self):
        page = tk.Frame(self.content_frame, bg=C['bg'])
        self.pages['objectifs'] = page

        # En-tête fixe
        header = tk.Frame(page, bg=C['bg'], pady=16)
        header.pack(fill='x', padx=30)
        tk.Label(header, text="🎯 Objectifs journaliers",
                 bg=C['bg'], fg=C['text'], font=FONT_TITLE).pack(side='left')
        tk.Button(header, text="💾  Sauvegarder",
                  bg=C['accent'], fg='white', font=FONT_BOLD,
                  relief='flat', cursor='hand2', padx=18, pady=9,
                  activebackground=C['accent_dim'],
                  command=self._sauvegarder_objectifs_manuels).pack(side='right')

        # ScrollFrame couvre tout le reste
        sf = ScrollFrame(page)
        sf.pack(fill='both', expand=True)
        inner = sf.inner
        inner.configure(padx=30, pady=10)

        # Bloc 1 : Progression du jour
        bloc1 = tk.Frame(inner, bg=C['surface2'], padx=22, pady=18)
        bloc1.pack(fill='x', pady=(0, 14))
        tk.Label(bloc1, text="Progression du jour vs objectifs",
                 bg=C['surface2'], fg=C['text'], font=FONT_H2).pack(anchor='w', pady=(0, 12))
        self.frame_obj_barres = tk.Frame(bloc1, bg=C['surface2'])
        self.frame_obj_barres.pack(fill='x')

        # Bloc 2 : Modification manuelle
        bloc2 = tk.Frame(inner, bg=C['surface2'], padx=22, pady=18)
        bloc2.pack(fill='x', pady=(0, 14))
        tk.Label(bloc2, text="Modifier les objectifs manuellement",
                 bg=C['surface2'], fg=C['text'], font=FONT_H2).pack(anchor='w', pady=(0, 4))
        tk.Label(bloc2, text="Ces valeurs ecrasent le calcul automatique du profil.",
                 bg=C['surface2'], fg=C['text_muted'], font=FONT_SMALL).pack(anchor='w', pady=(0, 14))

        self.vars_obj_manuels = {}
        nutriments_obj = [
            ('🔥 Calories (kcal)', 'calories', C['cal']),
            ('💪 Proteines (g)',   'proteines', C['prot']),
            ('🌾 Glucides (g)',    'glucides',  C['gluc']),
            ('🍬 Sucres (g)',      'sucres',    C['sucres_c']),
            ('🫒 Lipides (g)',     'lipides',   C['lip']),
            ('🌿 Fibres (g)',      'fibres',    C['fibres']),
            ('🧂 Sel (g)',         'sel',       C['sel_c']),
        ]
        grid_obj = tk.Frame(bloc2, bg=C['surface2'])
        grid_obj.pack(fill='x')
        obj = charger_objectifs()

        for i, (label, cle, couleur) in enumerate(nutriments_obj):
            col = i % 2
            row = i // 2
            card = tk.Frame(grid_obj, bg=C['surface3'], padx=14, pady=12)
            card.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
            grid_obj.columnconfigure(col, weight=1)
            tk.Label(card, text=label, bg=C['surface3'],
                     fg=C['text_muted'], font=FONT_SMALL).pack(anchor='w')
            var = tk.StringVar(value=str(obj.get(cle, 0)))
            tk.Entry(card, textvariable=var,
                     bg=C['bg'], fg=couleur, insertbackground=couleur,
                     font=('Segoe UI', 15, 'bold'),
                     relief='flat', bd=4, width=10).pack(anchor='w', pady=(6, 0))
            self.vars_obj_manuels[cle] = var

        # Bloc 3 : Recalcul auto
        bloc3 = tk.Frame(inner, bg=C['surface2'], padx=22, pady=18)
        bloc3.pack(fill='x', pady=(0, 14))
        tk.Label(bloc3, text="Recalcul automatique depuis le profil",
                 bg=C['surface2'], fg=C['text'], font=FONT_H2).pack(anchor='w', pady=(0, 6))
        profil = charger_profil()
        tk.Label(bloc3,
                 text=(f"Profil : {profil.poids_kg} kg · {profil.taille_cm} cm · "
                       f"{profil.age} ans · {profil.activite} · TDEE {profil.calcul_tdee()} kcal"),
                 bg=C['surface2'], fg=C['text_muted'], font=FONT_SMALL).pack(anchor='w', pady=(0, 12))

        btn_frame3 = tk.Frame(bloc3, bg=C['surface2'])
        btn_frame3.pack(anchor='w')
        for label_obj, objectif_val in [
            ("🔴  Seche", 'seche'),
            ("🟡  Maintien", 'maintien'),
            ("🟢  Prise de masse", 'prise_masse'),
        ]:
            tk.Button(btn_frame3, text=label_obj,
                      bg=C['surface3'], fg=C['text'], font=FONT_BODY,
                      relief='flat', cursor='hand2', padx=16, pady=9,
                      activebackground=C['hover'],
                      command=lambda o=objectif_val: self._appliquer_objectif_auto(o)
                      ).pack(side='left', padx=5)

        # Bloc 4 : Repartition
        bloc4 = tk.Frame(inner, bg=C['surface2'], padx=22, pady=18)
        bloc4.pack(fill='x', pady=(0, 20))
        tk.Label(bloc4, text="Repartition calorique",
                 bg=C['surface2'], fg=C['text'], font=FONT_H2).pack(anchor='w', pady=(0, 12))
        self.frame_repartition = tk.Frame(bloc4, bg=C['surface2'])
        self.frame_repartition.pack(fill='x')
        self._afficher_repartition()

    def _rafraichir_objectifs(self):
        """Met à jour les barres de la page objectifs"""
        obj = charger_objectifs()
        entrees = charger_journal(self.date_courante)
        totaux = calculer_totaux(entrees)

        # Mise à jour des entrées manuelles
        for cle, var in self.vars_obj_manuels.items():
            var.set(str(obj.get(cle, 0)))

        # Reconstruire les barres
        for w in self.frame_obj_barres.winfo_children():
            w.destroy()

        items_barres = [
            ('calories',  '🔥 Calories',  'kcal', C['cal']),
            ('proteines', '💪 Protéines', 'g',    C['prot']),
            ('glucides',  '🌾 Glucides',  'g',    C['gluc']),
            ('sucres',    '🍬 Sucres',    'g',    '#e91e8c'),
            ('lipides',   '🫒 Lipides',   'g',    C['lip']),
            ('fibres',    '🌿 Fibres',    'g',    C['fibres']),
            ('sel',       '🧂 Sel',       'g',    C['text_muted']),
        ]
        for cle, label, unite, couleur in items_barres:
            valeur = getattr(totaux, cle, 0)
            objectif = obj.get(cle, 1)
            pct = min(valeur / objectif, 1.0) if objectif else 0
            pct_txt = int(pct * 100)

            row = tk.Frame(self.frame_obj_barres, bg=C['surface2'])
            row.pack(fill='x', pady=4)

            top = tk.Frame(row, bg=C['surface2'])
            top.pack(fill='x')
            tk.Label(top, text=label, bg=C['surface2'],
                     fg=C['text'], font=FONT_BODY).pack(side='left')
            couleur_pct = C['success'] if 80 <= pct_txt <= 115 else (C['danger'] if pct_txt > 115 else C['warning'])
            tk.Label(top,
                     text=f"{valeur:.0f} / {objectif} {unite}  ({pct_txt}%)",
                     bg=C['surface2'], fg=couleur_pct,
                     font=FONT_SMALL).pack(side='right')

            # Barre
            barre_bg = tk.Frame(row, bg=C['surface2'], height=12)
            barre_bg.pack(fill='x', pady=(2, 0))
            barre_bg.update_idletasks()
            w_total = barre_bg.winfo_width() or 600
            barre_fill = tk.Frame(barre_bg,
                                   bg=couleur if pct_txt <= 100 else C['danger'],
                                   height=12,
                                   width=int(w_total * pct))
            barre_fill.place(x=0, y=0)

        self._afficher_repartition()

    def _afficher_repartition(self):
        for w in self.frame_repartition.winfo_children():
            w.destroy()
        obj = charger_objectifs()
        cal = obj.get('calories', 2000) or 2000
        prot = obj.get('proteines', 0) * 4
        gluc = obj.get('glucides', 0) * 4
        lip = obj.get('lipides', 0) * 9
        total = prot + gluc + lip or 1

        items = [
            ('💪 Protéines', prot, C['prot']),
            ('🌾 Glucides',  gluc, C['gluc']),
            ('🫒 Lipides',   lip,  C['lip']),
        ]
        for label, kcal_macro, couleur in items:
            pct = int(kcal_macro / total * 100)
            row = tk.Frame(self.frame_repartition, bg=C['surface2'],
                           padx=15, pady=12)
            row.pack(side='left', expand=True, fill='x', padx=5)
            tk.Label(row, text=label, bg=C['surface2'],
                     fg=C['text_muted'], font=FONT_SMALL).pack(anchor='w')
            tk.Label(row, text=f"{pct}%",
                     bg=C['surface2'], fg=couleur,
                     font=('Segoe UI', 22, 'bold')).pack(anchor='w')
            tk.Label(row, text=f"{kcal_macro:.0f} kcal",
                     bg=C['surface2'], fg=C['text_muted'],
                     font=FONT_SMALL).pack(anchor='w')

    def _sauvegarder_objectifs_manuels(self):
        try:
            import json
            data_path = os.path.join(BASE_DIR, 'data', 'objectifs.json')
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for cle, var in self.vars_obj_manuels.items():
                data['objectifs_journaliers'][cle] = float(var.get())
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.objectifs = charger_objectifs()
            messagebox.showinfo("Succès", "Objectifs sauvegardés !")
            self._rafraichir_objectifs()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def _appliquer_objectif_auto(self, objectif: str):
        profil = charger_profil()
        profil.objectif = objectif
        from database.db_manager import sauvegarder_profil
        sauvegarder_profil(profil)
        self.profil = profil
        self.objectifs = charger_objectifs()
        messagebox.showinfo("Objectif appliqué",
                            f"Objectifs recalculés pour : {objectif.replace('_', ' ').title()}")
        self._rafraichir_objectifs()

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE SUPPLÉMENTS
    # ═════════════════════════════════════════════════════════════════════════
    def _creer_page_supplements(self):
        page = tk.Frame(self.content_frame, bg=C['bg'])
        self.pages['supplements'] = page

        # ── En-tête ──────────────────────────────────────────────────────────
        header = tk.Frame(page, bg=C['bg'], pady=20)
        header.pack(fill='x', padx=30)
        tk.Label(header, text="🧪 Suppléments",
                 bg=C['bg'], fg=C['text'], font=FONT_TITLE).pack(side='left')
        tk.Button(header, text="+ Nouveau supplément",
                  bg=C['accent'], fg='white', font=FONT_BOLD,
                  relief='flat', cursor='hand2', padx=16, pady=9,
                  activebackground='#c73652',
                  command=self._dialog_nouveau_supplement).pack(side='right')

        # ── Info ─────────────────────────────────────────────────────────────
        info = tk.Frame(page, bg=C['surface'], padx=20, pady=12)
        info.pack(fill='x', padx=30, pady=(0, 15))
        tk.Label(info,
                 text="Gérez ici vos prises de suppléments quotidiennes (whey, créatine, vitamines…).\n"
                      "Chaque prise peut être ajoutée au journal du jour.",
                 bg=C['surface'], fg=C['text_muted'],
                 font=FONT_BODY, justify='left').pack(anchor='w')

        # ── Tabs : Prises du jour / Catalogue ────────────────────────────────
        nb = ttk.Notebook(page)
        nb.pack(fill='both', expand=True, padx=30, pady=(0, 20))

        # Tab 1 : Prises du jour
        tab_jour = tk.Frame(nb, bg=C['bg'])
        nb.add(tab_jour, text='  📅 Prises du jour  ')
        self._construire_tab_prises_jour(tab_jour)

        # Tab 2 : Catalogue suppléments
        tab_catalogue = tk.Frame(nb, bg=C['bg'])
        nb.add(tab_catalogue, text='  📋 Catalogue  ')
        self._construire_tab_catalogue(tab_catalogue)

        # Tab 3 : Suivi hebdomadaire
        tab_suivi = tk.Frame(nb, bg=C['bg'])
        nb.add(tab_suivi, text='  📊 Suivi hebdo  ')
        self._construire_tab_suivi(tab_suivi)

    def _construire_tab_prises_jour(self, parent):
        """Onglet des prises du jour"""
        top = tk.Frame(parent, bg=C['bg'])
        top.pack(fill='x', pady=10)

        tk.Label(top, text=f"Prises d'aujourd'hui ({date.today().strftime('%d/%m/%Y')})",
                 bg=C['bg'], fg=C['text'], font=FONT_H2).pack(side='left', padx=5)
        tk.Button(top, text="+ Enregistrer une prise",
                  bg=C['accent2'], fg='white', font=FONT_SMALL,
                  relief='flat', cursor='hand2', padx=12, pady=6,
                  activebackground='#7040a0',
                  command=self._dialog_prise_supplement).pack(side='right', padx=5)

        # Treeview prises du jour
        cols = ('heure', 'supplement', 'dose', 'cal', 'prot', 'note')
        self.tree_prises = ttk.Treeview(parent, columns=cols, show='headings', height=10)
        for col, label, w in [
            ('heure',       'Heure',         70),
            ('supplement',  'Supplément',   220),
            ('dose',        'Dose',          80),
            ('cal',         'Kcal',          70),
            ('prot',        'Prot.',         70),
            ('note',        'Note',         200),
        ]:
            self.tree_prises.heading(col, text=label)
            self.tree_prises.column(col, width=w, anchor='center')
        self.tree_prises.column('supplement', anchor='w')
        self.tree_prises.column('note', anchor='w')

        sc = ttk.Scrollbar(parent, orient='vertical', command=self.tree_prises.yview)
        self.tree_prises.configure(yscrollcommand=sc.set)
        sc.pack(side='right', fill='y')
        self.tree_prises.pack(fill='both', expand=True, padx=5)

        # Actions
        act = tk.Frame(parent, bg=C['bg'], pady=8)
        act.pack(fill='x', padx=5)
        tk.Button(act, text="➕ Ajouter au journal",
                  bg=C['surface'], fg=C['text'], font=FONT_SMALL,
                  relief='flat', cursor='hand2', padx=12, pady=5,
                  activebackground=C['hover'],
                  command=self._ajouter_prise_au_journal).pack(side='left', padx=5)
        tk.Button(act, text="🗑️ Supprimer",
                  bg=C['surface'], fg=C['text_muted'], font=FONT_SMALL,
                  relief='flat', cursor='hand2', padx=12, pady=5,
                  activebackground=C['hover'],
                  command=self._supprimer_prise).pack(side='left', padx=5)

        # Résumé du jour
        self.frame_resume_supps = tk.Frame(parent, bg=C['surface'], padx=15, pady=10)
        self.frame_resume_supps.pack(fill='x', padx=5, pady=8)
        self.lbl_resume_supps = tk.Label(self.frame_resume_supps,
                                          text="Total du jour : 0 kcal · 0g protéines",
                                          bg=C['surface'], fg=C['accent'], font=FONT_BOLD)
        self.lbl_resume_supps.pack(anchor='w')

    def _construire_tab_catalogue(self, parent):
        """Onglet catalogue de suppléments"""
        top = tk.Frame(parent, bg=C['bg'])
        top.pack(fill='x', pady=10, padx=5)
        tk.Label(top, text="Suppléments enregistrés",
                 bg=C['bg'], fg=C['text'], font=FONT_H2).pack(side='left')

        # Treeview catalogue
        cols = ('nom', 'type', 'dose_hab', 'cal', 'prot', 'note')
        self.tree_catalogue_supps = ttk.Treeview(parent, columns=cols, show='headings', height=12)
        for col, label, w in [
            ('nom',       'Nom',             200),
            ('type',      'Type',            120),
            ('dose_hab',  'Dose habituelle',  110),
            ('cal',       'Kcal/dose',         90),
            ('prot',      'Prot./dose',        90),
            ('note',      'Note',             180),
        ]:
            self.tree_catalogue_supps.heading(col, text=label)
            self.tree_catalogue_supps.column(col, width=w, anchor='center')
        self.tree_catalogue_supps.column('nom', anchor='w')
        self.tree_catalogue_supps.column('note', anchor='w')
        self.tree_catalogue_supps.bind('<Double-1>', lambda e: self._dialog_prise_supplement_depuis_catalogue())

        sc2 = make_tree_sb(parent, command=self.tree_catalogue_supps.yview)
        self.tree_catalogue_supps.configure(yscrollcommand=sc2.set)
        sc2.pack(side='right', fill='y')
        self.tree_catalogue_supps.pack(fill='both', expand=True, padx=5)

        act2 = tk.Frame(parent, bg=C['bg'], pady=8)
        act2.pack(fill='x', padx=5)
        for label, cmd in [
            ("✏️ Modifier",   self._modifier_supplement_catalogue),
            ("🗑️ Supprimer", self._supprimer_supplement_catalogue),
        ]:
            tk.Button(act2, text=label,
                      bg=C['surface'], fg=C['text_muted'], font=FONT_SMALL,
                      relief='flat', cursor='hand2', padx=12, pady=5,
                      activebackground=C['hover'],
                      command=cmd).pack(side='left', padx=5)

    def _construire_tab_suivi(self, parent):
        """Onglet suivi hebdomadaire des suppléments"""
        tk.Label(parent, text="Suivi des 7 derniers jours",
                 bg=C['bg'], fg=C['text'], font=FONT_H2).pack(pady=10, padx=5, anchor='w')

        self.frame_suivi_supps = tk.Frame(parent, bg=C['bg'])
        self.frame_suivi_supps.pack(fill='both', expand=True, padx=5)
        tk.Label(self.frame_suivi_supps,
                 text="Ouvrez l'onglet pour voir le suivi hebdomadaire.",
                 bg=C['bg'], fg=C['text_muted'], font=FONT_BODY).pack(pady=30)

    def _rafraichir_supplements(self):
        """Recharge toutes les données des suppléments"""
        import json, os
        supp_path = os.path.join(BASE_DIR, 'data', 'supplements.json')
        try:
            with open(supp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {'supplements': [], 'prises': {}}

        self._supps_data = data
        self._rafraichir_catalogue_supps()
        self._rafraichir_prises_jour()

    def _rafraichir_catalogue_supps(self):
        if not hasattr(self, 'tree_catalogue_supps'):
            return
        self.tree_catalogue_supps.delete(*self.tree_catalogue_supps.get_children())
        for s in self._supps_data.get('supplements', []):
            self.tree_catalogue_supps.insert('', 'end', iid=s['id'], values=(
                s.get('nom', ''),
                s.get('type', ''),
                f"{s.get('dose_habituelle', 0)}g",
                f"{s.get('kcal_dose', 0):.0f}",
                f"{s.get('prot_dose', 0):.1f}g",
                s.get('note', ''),
            ))

    def _rafraichir_prises_jour(self):
        if not hasattr(self, 'tree_prises'):
            return
        self.tree_prises.delete(*self.tree_prises.get_children())
        today = date.today().isoformat()
        prises = self._supps_data.get('prises', {}).get(today, [])
        total_cal = 0
        total_prot = 0
        for p in prises:
            total_cal += p.get('kcal', 0)
            total_prot += p.get('prot', 0)
            self.tree_prises.insert('', 'end', iid=p.get('id_prise', ''), values=(
                p.get('heure', ''),
                p.get('nom', ''),
                f"{p.get('dose_g', 0)}g",
                f"{p.get('kcal', 0):.0f}",
                f"{p.get('prot', 0):.1f}g",
                p.get('note', ''),
            ))
        if hasattr(self, 'lbl_resume_supps'):
            self.lbl_resume_supps.configure(
                text=f"Total du jour : {total_cal:.0f} kcal · {total_prot:.1f}g protéines"
            )

    def _dialog_nouveau_supplement(self):
        dialog = DialogSupplementForm(self)
        self.wait_window(dialog)
        if dialog.resultat:
            self._sauvegarder_supplement(dialog.resultat)

    def _dialog_prise_supplement(self, supplement=None):
        supps = self._supps_data.get('supplements', [])
        if not supps:
            messagebox.showinfo("Info", "Ajoutez d'abord un supplément dans le catalogue.")
            return
        dialog = DialogPriseSupplementForm(self, supps, supplement)
        self.wait_window(dialog)
        if dialog.resultat:
            self._enregistrer_prise(dialog.resultat)

    def _dialog_prise_supplement_depuis_catalogue(self):
        sel = self.tree_catalogue_supps.selection()
        if not sel:
            return
        supps = self._supps_data.get('supplements', [])
        supplement = next((s for s in supps if s['id'] == sel[0]), None)
        self._dialog_prise_supplement(supplement)

    def _sauvegarder_supplement(self, supp: dict):
        import json, os
        supp_path = os.path.join(BASE_DIR, 'data', 'supplements.json')
        try:
            with open(supp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {'supplements': [], 'prises': {}}
        if 'supplements' not in data:
            data['supplements'] = []
        # Modifier ou ajouter
        ids_existants = [s['id'] for s in data['supplements']]
        if supp['id'] in ids_existants:
            data['supplements'] = [supp if s['id'] == supp['id'] else s
                                    for s in data['supplements']]
        else:
            data['supplements'].append(supp)
        with open(supp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self._rafraichir_supplements()

    def _enregistrer_prise(self, prise: dict):
        import json, os
        supp_path = os.path.join(BASE_DIR, 'data', 'supplements.json')
        try:
            with open(supp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {'supplements': [], 'prises': {}}
        if 'prises' not in data:
            data['prises'] = {}
        today = date.today().isoformat()
        if today not in data['prises']:
            data['prises'][today] = []
        data['prises'][today].append(prise)
        with open(supp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self._rafraichir_supplements()

    def _ajouter_prise_au_journal(self):
        """Ajoute la prise sélectionnée au journal alimentaire"""
        sel = self.tree_prises.selection()
        if not sel:
            messagebox.showinfo("Info", "Sélectionnez une prise à ajouter au journal.")
            return
        id_prise = sel[0]
        today = date.today().isoformat()
        prises = self._supps_data.get('prises', {}).get(today, [])
        prise = next((p for p in prises if p.get('id_prise') == id_prise), None)
        if not prise:
            return
        # Chercher l'aliment correspondant dans la base
        aliments = charger_aliments()
        aliment = next((a for a in aliments if a.nom.lower() in prise['nom'].lower()
                        or prise['nom'].lower() in a.nom.lower()), None)
        if aliment:
            self._ouvrir_dialog_ajout(aliment)
        else:
            # Créer une entrée directe avec les valeurs de la prise
            valeurs = ValeursNutritionnelles(
                calories=prise.get('kcal', 0),
                proteines=prise.get('prot', 0),
            )
            entree = EntreeJournal(
                aliment_id='supp_' + id_prise,
                aliment_nom=prise['nom'],
                quantite_g=prise.get('dose_g', 0),
                valeurs_calculees=valeurs,
                repas='Collation',
                heure=datetime.now().strftime('%H:%M'),
            )
            ajouter_entree_journal(entree, self.date_courante)
            messagebox.showinfo("Ajouté", f"{prise['nom']} ajouté au journal !")

    def _supprimer_prise(self):
        sel = self.tree_prises.selection()
        if not sel:
            return
        id_prise = sel[0]
        import json, os
        supp_path = os.path.join(BASE_DIR, 'data', 'supplements.json')
        try:
            with open(supp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            today = date.today().isoformat()
            data['prises'][today] = [p for p in data['prises'].get(today, [])
                                      if p.get('id_prise') != id_prise]
            with open(supp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._rafraichir_supplements()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def _modifier_supplement_catalogue(self):
        sel = self.tree_catalogue_supps.selection()
        if not sel:
            messagebox.showinfo("Info", "Sélectionnez un supplément à modifier.")
            return
        supps = self._supps_data.get('supplements', [])
        supp = next((s for s in supps if s['id'] == sel[0]), None)
        if supp:
            dialog = DialogSupplementForm(self, supp)
            self.wait_window(dialog)
            if dialog.resultat:
                self._sauvegarder_supplement(dialog.resultat)

    def _supprimer_supplement_catalogue(self):
        sel = self.tree_catalogue_supps.selection()
        if not sel:
            return
        if not messagebox.askyesno("Confirmer", "Supprimer ce supplément du catalogue ?"):
            return
        import json, os
        supp_path = os.path.join(BASE_DIR, 'data', 'supplements.json')
        try:
            with open(supp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data['supplements'] = [s for s in data.get('supplements', [])
                                    if s['id'] != sel[0]]
            with open(supp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._rafraichir_supplements()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# DIALOGUES SUPPLÉMENTS
# ═══════════════════════════════════════════════════════════════════════════════

class DialogSupplementForm(tk.Toplevel):
    """Formulaire création / modification d'un supplément"""

    TYPES = ['Protéine', 'Créatine', 'Vitamine', 'Minéral', 'Acides gras',
             'Pré-workout', 'Gainer', 'BCAA', 'Brûleur', 'Autre']

    def __init__(self, parent, supp: dict = None):
        super().__init__(parent)
        self.title("Nouveau supplément" if supp is None else "Modifier le supplément")
        self.configure(bg=C['bg'])
        self.geometry("480x520")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.resultat = None
        self._supp = supp
        self._construire()

    def _construire(self):
        tk.Label(self, text="Informations du supplément",
                 bg=C['bg'], fg=C['text'], font=FONT_H2).pack(pady=15, padx=25, anchor='w')

        form = tk.Frame(self, bg=C['bg'])
        form.pack(fill='both', expand=True, padx=25)

        s = self._supp or {}
        champs = [
            ('Nom *',                    'nom',             s.get('nom', '')),
            ('Type',                     'type',            s.get('type', 'Protéine')),
            ('Dose habituelle (g)',       'dose_habituelle', str(s.get('dose_habituelle', 30))),
            ('Kcal par dose',            'kcal_dose',       str(s.get('kcal_dose', 0))),
            ('Protéines par dose (g)',   'prot_dose',       str(s.get('prot_dose', 0))),
            ('Glucides par dose (g)',    'gluc_dose',       str(s.get('gluc_dose', 0))),
            ('Lipides par dose (g)',     'lip_dose',        str(s.get('lip_dose', 0))),
            ('Marque',                   'marque',          s.get('marque', '')),
            ('Note personnelle',         'note',            s.get('note', '')),
        ]
        self.vars_supp = {}
        for i, (label, cle, val) in enumerate(champs):
            tk.Label(form, text=label, bg=C['bg'],
                     fg=C['text'], font=FONT_BODY).grid(
                row=i, column=0, sticky='w', pady=4, padx=(0, 15))
            if cle == 'type':
                var = tk.StringVar(value=val)
                ttk.Combobox(form, textvariable=var,
                             values=self.TYPES, state='readonly', width=25).grid(
                    row=i, column=1, sticky='w', pady=4)
            else:
                var = tk.StringVar(value=val)
                tk.Entry(form, textvariable=var,
                         bg=C['surface2'], fg=C['text'],
                         insertbackground=C['text'],
                         font=FONT_BODY, relief='flat', bd=5, width=28).grid(
                    row=i, column=1, sticky='w', pady=4)
            self.vars_supp[cle] = var

        btn_frame = tk.Frame(self, bg=C['bg'])
        btn_frame.pack(fill='x', padx=25, pady=15)
        tk.Button(btn_frame, text="Annuler", bg=C['surface'], fg=C['text'],
                  relief='flat', cursor='hand2', padx=12, pady=7,
                  activebackground=C['hover'],
                  command=self.destroy).pack(side='right', padx=5)
        tk.Button(btn_frame, text="✓ Enregistrer", bg=C['accent'], fg='white',
                  font=FONT_BOLD, relief='flat', cursor='hand2', padx=12, pady=7,
                  activebackground='#c73652',
                  command=self._valider).pack(side='right', padx=5)

    def _valider(self):
        nom = self.vars_supp['nom'].get().strip()
        if not nom:
            messagebox.showerror("Erreur", "Le nom est obligatoire")
            return
        try:
            supp = {
                'id': self._supp['id'] if self._supp else str(uuid.uuid4())[:8],
                'nom': nom,
                'type': self.vars_supp['type'].get(),
                'dose_habituelle': float(self.vars_supp['dose_habituelle'].get() or 0),
                'kcal_dose': float(self.vars_supp['kcal_dose'].get() or 0),
                'prot_dose': float(self.vars_supp['prot_dose'].get() or 0),
                'gluc_dose': float(self.vars_supp['gluc_dose'].get() or 0),
                'lip_dose':  float(self.vars_supp['lip_dose'].get() or 0),
                'marque': self.vars_supp['marque'].get(),
                'note': self.vars_supp['note'].get(),
            }
        except ValueError:
            messagebox.showerror("Erreur", "Valeurs numériques invalides")
            return
        self.resultat = supp
        self.destroy()


class DialogPriseSupplementForm(tk.Toplevel):
    """Dialogue pour enregistrer une prise de supplément"""

    def __init__(self, parent, supplements: list, supplement_prefill=None):
        super().__init__(parent)
        self.title("Enregistrer une prise")
        self.configure(bg=C['bg'])
        self.geometry("420x320")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.resultat = None
        self._supplements = supplements
        self._supp_sel = supplement_prefill
        self._construire()

    def _construire(self):
        tk.Label(self, text="Enregistrer une prise",
                 bg=C['bg'], fg=C['text'], font=FONT_H2).pack(pady=15, padx=20, anchor='w')

        form = tk.Frame(self, bg=C['bg'], padx=20)
        form.pack(fill='x')

        # Sélection supplément
        tk.Label(form, text="Supplément :", bg=C['bg'],
                 fg=C['text'], font=FONT_BODY).grid(row=0, column=0, sticky='w', pady=6)
        noms = [s['nom'] for s in self._supplements]
        val_init = self._supp_sel['nom'] if self._supp_sel else (noms[0] if noms else '')
        self.var_nom = tk.StringVar(value=val_init)
        cb = ttk.Combobox(form, textvariable=self.var_nom,
                          values=noms, state='readonly', width=28)
        cb.grid(row=0, column=1, sticky='w', pady=6, padx=(10, 0))
        cb.bind('<<ComboboxSelected>>', self._on_supp_change)

        # Dose
        tk.Label(form, text="Dose (g) :", bg=C['bg'],
                 fg=C['text'], font=FONT_BODY).grid(row=1, column=0, sticky='w', pady=6)
        dose_init = str(self._supp_sel.get('dose_habituelle', 30)) if self._supp_sel else '30'
        self.var_dose = tk.StringVar(value=dose_init)
        tk.Entry(form, textvariable=self.var_dose, width=10,
                 bg=C['surface2'], fg=C['text'],
                 insertbackground=C['text'],
                 font=FONT_BODY, relief='flat', bd=5).grid(
            row=1, column=1, sticky='w', pady=6, padx=(10, 0))

        # Heure
        tk.Label(form, text="Heure :", bg=C['bg'],
                 fg=C['text'], font=FONT_BODY).grid(row=2, column=0, sticky='w', pady=6)
        self.var_heure = tk.StringVar(value=datetime.now().strftime('%H:%M'))
        tk.Entry(form, textvariable=self.var_heure, width=10,
                 bg=C['surface2'], fg=C['text'],
                 insertbackground=C['text'],
                 font=FONT_BODY, relief='flat', bd=5).grid(
            row=2, column=1, sticky='w', pady=6, padx=(10, 0))

        # Note
        tk.Label(form, text="Note :", bg=C['bg'],
                 fg=C['text'], font=FONT_BODY).grid(row=3, column=0, sticky='w', pady=6)
        self.var_note = tk.StringVar()
        tk.Entry(form, textvariable=self.var_note, width=28,
                 bg=C['surface2'], fg=C['text'],
                 insertbackground=C['text'],
                 font=FONT_BODY, relief='flat', bd=5).grid(
            row=3, column=1, sticky='w', pady=6, padx=(10, 0))

        # Preview valeurs nutritionnelles
        self.lbl_preview_prise = tk.Label(self, text="",
                                           bg=C['surface'], fg=C['text_muted'],
                                           font=FONT_SMALL, padx=15, pady=8)
        self.lbl_preview_prise.pack(fill='x', padx=20, pady=8)
        self._maj_preview()
        self.var_dose.trace('w', lambda *a: self._maj_preview())

        # Boutons
        btn_frame = tk.Frame(self, bg=C['bg'])
        btn_frame.pack(fill='x', padx=20, pady=10)
        tk.Button(btn_frame, text="Annuler", bg=C['surface'], fg=C['text'],
                  relief='flat', cursor='hand2', padx=12, pady=7,
                  activebackground=C['hover'],
                  command=self.destroy).pack(side='right', padx=5)
        tk.Button(btn_frame, text="✓ Enregistrer", bg=C['accent'], fg='white',
                  font=FONT_BOLD, relief='flat', cursor='hand2', padx=12, pady=7,
                  activebackground='#c73652',
                  command=self._valider).pack(side='right', padx=5)

    def _on_supp_change(self, event=None):
        nom = self.var_nom.get()
        self._supp_sel = next((s for s in self._supplements if s['nom'] == nom), None)
        if self._supp_sel:
            self.var_dose.set(str(self._supp_sel.get('dose_habituelle', 30)))
        self._maj_preview()

    def _maj_preview(self):
        if not self._supp_sel:
            return
        try:
            dose = float(self.var_dose.get() or 0)
            dose_ref = self._supp_sel.get('dose_habituelle', 30) or 30
            facteur = dose / dose_ref
            kcal = self._supp_sel.get('kcal_dose', 0) * facteur
            prot = self._supp_sel.get('prot_dose', 0) * facteur
            gluc = self._supp_sel.get('gluc_dose', 0) * facteur
            lip  = self._supp_sel.get('lip_dose', 0) * facteur
            self.lbl_preview_prise.configure(
                text=f"Pour {dose:.0f}g : {kcal:.0f} kcal · {prot:.1f}g prot · "
                     f"{gluc:.1f}g gluc · {lip:.1f}g lip"
            )
        except (ValueError, ZeroDivisionError):
            self.lbl_preview_prise.configure(text="Dose invalide")

    def _valider(self):
        nom = self.var_nom.get()
        if not nom:
            messagebox.showerror("Erreur", "Sélectionnez un supplément")
            return
        try:
            dose = float(self.var_dose.get() or 0)
            if dose <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "Dose invalide")
            return

        supp = self._supp_sel or {}
        dose_ref = supp.get('dose_habituelle', 30) or 30
        facteur = dose / dose_ref

        self.resultat = {
            'id_prise': str(uuid.uuid4())[:8],
            'nom': nom,
            'dose_g': dose,
            'heure': self.var_heure.get(),
            'note': self.var_note.get(),
            'kcal': round(supp.get('kcal_dose', 0) * facteur, 1),
            'prot': round(supp.get('prot_dose', 0) * facteur, 1),
            'gluc': round(supp.get('gluc_dose', 0) * facteur, 1),
            'lip':  round(supp.get('lip_dose', 0) * facteur, 1),
        }
        self.destroy()


class DialogAjoutAliment(tk.Toplevel):
    """Dialogue de sélection d'aliment et saisie de quantité pour le journal"""

    def __init__(self, parent, aliment_prefill: Aliment = None):
        super().__init__(parent)
        self.title("Ajouter au journal")
        self.configure(bg=C['bg'])
        self.resizable(True, True)
        self.geometry("700x600")
        self.transient(parent)
        self.grab_set()
        self.resultat = None
        self._aliment_selectionne = aliment_prefill
        self._tous_les_aliments = charger_aliments()
        self._construire()
        if aliment_prefill:
            self._afficher_aliment(aliment_prefill)

    def _construire(self):
        tk.Label(self, text="Ajouter un aliment au journal",
                 bg=C['bg'], fg=C['text'], font=FONT_H2).pack(pady=15, padx=20, anchor='w')

        # Recherche
        search_frame = tk.Frame(self, bg=C['surface'], padx=10, pady=8)
        search_frame.pack(fill='x', padx=20, pady=(0, 10))

        tk.Label(search_frame, text="🔍", bg=C['surface'],
                 fg=C['text_muted'], font=('Segoe UI', 14)).pack(side='left')
        self.var_search = tk.StringVar()
        self.var_search.trace('w', self._filtrer)
        entry = tk.Entry(search_frame, textvariable=self.var_search,
                         bg=C['surface2'], fg=C['text'],
                         insertbackground=C['text'],
                         font=FONT_BODY, relief='flat', bd=5)
        entry.pack(side='left', fill='x', expand=True, padx=8)
        entry.focus_set()

        # Liste
        list_frame = tk.Frame(self, bg=C['surface'])
        list_frame.pack(fill='both', expand=True, padx=20, pady=(0, 10))

        cols = ('nom', 'cal', 'prot')
        self.tree = ttk.Treeview(list_frame, columns=cols, show='headings',
                                  height=10, selectmode='browse')
        self.tree.heading('nom', text='Aliment')
        self.tree.heading('cal', text='Kcal/100g')
        self.tree.heading('prot', text='Prot./100g')
        self.tree.column('nom', width=350, anchor='w')
        self.tree.column('cal', width=100, anchor='center')
        self.tree.column('prot', width=100, anchor='center')
        sc = make_tree_sb(list_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sc.set)
        sc.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Double-1>', lambda e: self._valider())
        self._charger_liste()

        # Info aliment sélectionné
        self.frame_info = tk.Frame(self, bg=C['surface'], padx=15, pady=10)
        self.frame_info.pack(fill='x', padx=20, pady=(0, 10))
        self.lbl_info = tk.Label(self.frame_info, text="Sélectionnez un aliment",
                                  bg=C['surface'], fg=C['text_muted'], font=FONT_SMALL)
        self.lbl_info.pack(anchor='w')

        # Quantité et repas
        bottom = tk.Frame(self, bg=C['bg'])
        bottom.pack(fill='x', padx=20, pady=(0, 15))

        tk.Label(bottom, text="Quantité (g) :",
                 bg=C['bg'], fg=C['text'], font=FONT_BODY).pack(side='left')
        self.var_quantite = tk.StringVar(value="100")
        entry_q = tk.Entry(bottom, textvariable=self.var_quantite, width=8,
                           bg=C['surface2'], fg=C['text'],
                           insertbackground=C['text'],
                           font=FONT_BODY, relief='flat', bd=5)
        entry_q.pack(side='left', padx=10)
        self.var_quantite.trace('w', self._preview_valeurs)

        tk.Label(bottom, text="Repas :",
                 bg=C['bg'], fg=C['text'], font=FONT_BODY).pack(side='left')
        self.var_repas = tk.StringVar(value="Déjeuner")
        combo_repas = ttk.Combobox(bottom, textvariable=self.var_repas,
                                    values=REPAS_OPTIONS, state='readonly', width=15)
        combo_repas.pack(side='left', padx=10)

        # Preview valeurs
        self.lbl_preview = tk.Label(bottom, text="",
                                     bg=C['bg'], fg=C['text_muted'], font=FONT_SMALL)
        self.lbl_preview.pack(side='left', padx=10)

        # Boutons
        btn_frame = tk.Frame(self, bg=C['bg'])
        btn_frame.pack(fill='x', padx=20, pady=(0, 15))
        tk.Button(btn_frame, text="Annuler", bg=C['surface'], fg=C['text'],
                  font=FONT_BODY, relief='flat', cursor='hand2', padx=15, pady=8,
                  activebackground=C['hover'],
                  command=self.destroy).pack(side='right', padx=5)
        tk.Button(btn_frame, text="✓ Ajouter", bg=C['accent'], fg='white',
                  font=FONT_BOLD, relief='flat', cursor='hand2', padx=15, pady=8,
                  activebackground='#c73652',
                  command=self._valider).pack(side='right', padx=5)

    def _charger_liste(self, aliments=None):
        self.tree.delete(*self.tree.get_children())
        for a in (aliments or self._tous_les_aliments):
            self.tree.insert('', 'end', iid=a.id, values=(
                str(a), f"{a.valeurs_100g.calories:.0f}", f"{a.valeurs_100g.proteines:.1f}"
            ))

    def _filtrer(self, *args):
        query = self.var_search.get().strip()
        if query:
            resultats = rechercher_aliment(query)
        else:
            resultats = self._tous_les_aliments
        self._charger_liste(resultats)

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        aliment = next((a for a in self._tous_les_aliments if a.id == sel[0]), None)
        if aliment:
            self._afficher_aliment(aliment)

    def _afficher_aliment(self, aliment: Aliment):
        self._aliment_selectionne = aliment
        v = aliment.valeurs_100g
        self.lbl_info.configure(
            text=f"{aliment.nom}  |  pour 100g : {v.calories:.0f} kcal · "
                 f"{v.proteines:.1f}g prot · {v.glucides:.1f}g gluc · {v.lipides:.1f}g lip",
            fg=C['text']
        )
        self._preview_valeurs()

    def _preview_valeurs(self, *args):
        if not self._aliment_selectionne:
            return
        try:
            q = float(self.var_quantite.get())
            v = self._aliment_selectionne.valeurs_100g.calculer_pour_quantite(q)
            self.lbl_preview.configure(
                text=f"→ {v.calories:.0f} kcal · {v.proteines:.1f}g prot · "
                     f"{v.glucides:.1f}g gluc · {v.lipides:.1f}g lip"
            )
        except ValueError:
            self.lbl_preview.configure(text="Quantité invalide")

    def _valider(self):
        if not self._aliment_selectionne:
            messagebox.showwarning("Info", "Sélectionnez un aliment")
            return
        try:
            q = float(self.var_quantite.get())
            if q <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "Quantité invalide")
            return
        self.resultat = (self._aliment_selectionne, q, self.var_repas.get())
        self.destroy()


class DialogModifierEntree(tk.Toplevel):
    """Dialogue de modification d'une entrée du journal"""

    def __init__(self, parent, entree: EntreeJournal):
        super().__init__(parent)
        self.title("Modifier l'entrée")
        self.configure(bg=C['bg'])
        self.geometry("380x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.resultat = None

        tk.Label(self, text=f"Modifier : {entree.aliment_nom}",
                 bg=C['bg'], fg=C['text'], font=FONT_H2).pack(pady=15, padx=20, anchor='w')

        frame = tk.Frame(self, bg=C['bg'])
        frame.pack(fill='x', padx=20)

        tk.Label(frame, text="Quantité (g) :", bg=C['bg'],
                 fg=C['text'], font=FONT_BODY).pack(side='left')
        self.var_q = tk.StringVar(value=str(entree.quantite_g))
        tk.Entry(frame, textvariable=self.var_q, width=8,
                 bg=C['surface2'], fg=C['text'],
                 insertbackground=C['text'],
                 font=FONT_BODY, relief='flat', bd=5).pack(side='left', padx=10)

        tk.Label(frame, text="Repas :", bg=C['bg'],
                 fg=C['text'], font=FONT_BODY).pack(side='left')
        self.var_repas = tk.StringVar(value=entree.repas.capitalize())
        ttk.Combobox(frame, textvariable=self.var_repas,
                     values=REPAS_OPTIONS, state='readonly', width=14).pack(side='left', padx=5)

        btn_frame = tk.Frame(self, bg=C['bg'])
        btn_frame.pack(fill='x', padx=20, pady=20)
        tk.Button(btn_frame, text="Annuler", bg=C['surface'], fg=C['text'],
                  relief='flat', cursor='hand2', padx=12, pady=7,
                  activebackground=C['hover'],
                  command=self.destroy).pack(side='right', padx=5)
        tk.Button(btn_frame, text="✓ Sauvegarder", bg=C['accent'], fg='white',
                  font=FONT_BOLD, relief='flat', cursor='hand2', padx=12, pady=7,
                  activebackground='#c73652',
                  command=self._valider).pack(side='right', padx=5)

    def _valider(self):
        try:
            q = float(self.var_q.get())
            if q <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "Quantité invalide")
            return
        self.resultat = (q, self.var_repas.get())
        self.destroy()


class DialogAlimentForm(tk.Toplevel):
    """Formulaire de création / modification d'un aliment"""

    def __init__(self, parent, aliment: Aliment = None):
        super().__init__(parent)
        self.title("Nouvel aliment" if aliment is None else "Modifier l'aliment")
        self.configure(bg=C['bg'])
        self.geometry("500x580")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.resultat = None
        self._aliment = aliment
        self._construire()

    def _construire(self):
        tk.Label(self, text="Informations générales",
                 bg=C['bg'], fg=C['text'], font=FONT_H2).pack(pady=10, padx=20, anchor='w')

        form = tk.Frame(self, bg=C['bg'])
        form.pack(fill='both', expand=True, padx=20)

        a = self._aliment
        cats = ['viandes', 'poissons', 'oeufs', 'feculents', 'legumes', 'fruits',
                'laitiers', 'oleagineux', 'legumineuses', 'complements', 'boissons',
                'matieres_grasses', 'charcuterie', 'sucres', 'proteines_veg', 'autre']

        champs_info = [
            ('Nom *', 'nom', 'entry', a.nom if a else ''),
            ('Marque', 'marque', 'entry', a.marque if a else 'Standard'),
            ('Catégorie', 'categorie', 'combo', cats, a.categorie if a else 'autre'),
        ]

        self.vars = {}
        for i, champ in enumerate(champs_info):
            tk.Label(form, text=champ[0], bg=C['bg'],
                     fg=C['text'], font=FONT_BODY).grid(
                row=i, column=0, sticky='w', pady=5, padx=(0, 15))
            if champ[2] == 'entry':
                var = tk.StringVar(value=champ[3])
                tk.Entry(form, textvariable=var, bg=C['surface2'], fg=C['text'],
                         insertbackground=C['text'],
                         font=FONT_BODY, relief='flat', bd=5, width=30).grid(
                    row=i, column=1, sticky='w', pady=5)
            else:
                var = tk.StringVar(value=champ[4])
                ttk.Combobox(form, textvariable=var,
                             values=champ[3], state='readonly', width=27).grid(
                    row=i, column=1, sticky='w', pady=5)
            self.vars[champ[1]] = var

        tk.Label(form, text="Valeurs nutritionnelles pour 100g :",
                 bg=C['bg'], fg=C['text_muted'], font=FONT_SMALL).grid(
            row=4, column=0, columnspan=2, sticky='w', pady=(15, 5))

        v = a.valeurs_100g if a else ValeursNutritionnelles()
        nutriments = [
            ('Calories (kcal)', 'calories', str(v.calories)),
            ('Protéines (g)', 'proteines', str(v.proteines)),
            ('Glucides (g)', 'glucides', str(v.glucides)),
            ('dont Sucres (g)', 'sucres', str(v.sucres)),
            ('Lipides (g)', 'lipides', str(v.lipides)),
            ('dont AG saturés (g)', 'acides_gras_satures', str(v.acides_gras_satures)),
            ('Fibres (g)', 'fibres', str(v.fibres)),
            ('Sel (g)', 'sel', str(v.sel)),
        ]

        for i, (label, cle, val) in enumerate(nutriments):
            row = 5 + i
            tk.Label(form, text=label, bg=C['bg'],
                     fg=C['text'], font=FONT_BODY).grid(
                row=row, column=0, sticky='w', pady=3, padx=(0, 15))
            var = tk.StringVar(value=val)
            tk.Entry(form, textvariable=var, bg=C['surface2'], fg=C['text'],
                     insertbackground=C['text'],
                     font=FONT_BODY, relief='flat', bd=5, width=12).grid(
                row=row, column=1, sticky='w', pady=3)
            self.vars[cle] = var

        btn_frame = tk.Frame(self, bg=C['bg'])
        btn_frame.pack(fill='x', padx=20, pady=15)
        tk.Button(btn_frame, text="Annuler", bg=C['surface'], fg=C['text'],
                  relief='flat', cursor='hand2', padx=12, pady=7,
                  activebackground=C['hover'],
                  command=self.destroy).pack(side='right', padx=5)
        tk.Button(btn_frame, text="✓ Enregistrer", bg=C['accent'], fg='white',
                  font=FONT_BOLD, relief='flat', cursor='hand2', padx=12, pady=7,
                  activebackground='#c73652',
                  command=self._valider).pack(side='right', padx=5)

    def _valider(self):
        nom = self.vars['nom'].get().strip()
        if not nom:
            messagebox.showerror("Erreur", "Le nom est obligatoire")
            return
        try:
            v = ValeursNutritionnelles(
                calories=float(self.vars['calories'].get()),
                proteines=float(self.vars['proteines'].get()),
                glucides=float(self.vars['glucides'].get()),
                sucres=float(self.vars['sucres'].get()),
                lipides=float(self.vars['lipides'].get()),
                acides_gras_satures=float(self.vars['acides_gras_satures'].get()),
                fibres=float(self.vars['fibres'].get()),
                sel=float(self.vars['sel'].get()),
            )
        except ValueError:
            messagebox.showerror("Erreur", "Valeurs numériques invalides")
            return

        if self._aliment:
            aliment = self._aliment
            aliment.nom = nom
            aliment.marque = self.vars['marque'].get()
            aliment.categorie = self.vars['categorie'].get()
            aliment.valeurs_100g = v
        else:
            aliment = Aliment(
                nom=nom,
                marque=self.vars['marque'].get() or 'Standard',
                categorie=self.vars['categorie'].get(),
                valeurs_100g=v,
            )
        self.resultat = aliment
        self.destroy()


class DialogAnalyseAliment(tk.Toplevel):
    """Fenêtre d'analyse nutritionnelle d'un aliment"""

    def __init__(self, parent, aliment: Aliment, objectif: str = 'maintien'):
        super().__init__(parent)
        self.title(f"Analyse — {aliment.nom}")
        self.configure(bg=C['bg'])
        self.geometry("550x550")
        self.transient(parent)
        self.grab_set()

        tk.Label(self, text=aliment.nom, bg=C['bg'],
                 fg=C['text'], font=FONT_TITLE).pack(pady=15, padx=20, anchor='w')

        # Score santé
        score = score_sante(aliment)
        couleur = couleur_score(score)
        score_frame = tk.Frame(self, bg=C['surface'], padx=20, pady=15)
        score_frame.pack(fill='x', padx=20, pady=(0, 10))
        tk.Label(score_frame, text="Score santé",
                 bg=C['surface'], fg=C['text_muted'], font=FONT_SMALL).pack(anchor='w')
        tk.Label(score_frame, text=f"{score}/100",
                 bg=C['surface'], fg=couleur, font=('Segoe UI', 28, 'bold')).pack(anchor='w')

        # Alertes
        alertes = analyser_aliment(aliment)
        alertes_frame = tk.Frame(self, bg=C['surface'], padx=20, pady=15)
        alertes_frame.pack(fill='x', padx=20, pady=(0, 10))
        tk.Label(alertes_frame, text="Analyse",
                 bg=C['surface'], fg=C['text'], font=FONT_H2).pack(anchor='w', pady=(0, 8))

        couleurs_alertes = {'ok': C['success'], 'info': C['info'],
                            'attention': C['warning'], 'danger': C['danger']}
        for type_alerte, msg in alertes:
            couleur_a = couleurs_alertes.get(type_alerte, C['text'])
            tk.Label(alertes_frame, text=f"{'✓' if type_alerte=='ok' else '⚠'} {msg}",
                     bg=C['surface'], fg=couleur_a, font=FONT_BODY,
                     wraplength=480, justify='left').pack(anchor='w', pady=2)

        # Suggestions
        sugg = suggestions_alternatives(aliment, objectif)
        sugg_frame = tk.Frame(self, bg=C['surface2'], padx=20, pady=15)
        sugg_frame.pack(fill='x', padx=20, pady=(0, 10))
        tk.Label(sugg_frame, text=f"Suggestions ({objectif.replace('_',' ')})",
                 bg=C['surface2'], fg=C['text'], font=FONT_H2).pack(anchor='w', pady=(0, 8))
        for s in sugg:
            tk.Label(sugg_frame, text=s, bg=C['surface2'],
                     fg=C['text_muted'], font=FONT_BODY,
                     wraplength=490, justify='left').pack(anchor='w', pady=2)

        tk.Button(self, text="Fermer", bg=C['accent'], fg='white',
                  font=FONT_BOLD, relief='flat', cursor='hand2',
                  padx=20, pady=8, activebackground='#c73652',
                  command=self.destroy).pack(pady=15)


class DialogAnalyseJournee(tk.Toplevel):
    """Fenêtre d'analyse nutritionnelle de la journée"""

    def __init__(self, parent, conseils):
        super().__init__(parent)
        self.title("Analyse de la journée")
        self.configure(bg=C['bg'])
        self.geometry("480x350")
        self.transient(parent)
        self.grab_set()

        tk.Label(self, text="Analyse nutritionnelle du jour",
                 bg=C['bg'], fg=C['text'], font=FONT_TITLE).pack(pady=15, padx=20, anchor='w')

        frame = tk.Frame(self, bg=C['surface'], padx=20, pady=20)
        frame.pack(fill='both', expand=True, padx=20, pady=(0, 15))

        couleurs = {'ok': C['success'], 'info': C['info'],
                    'attention': C['warning'], 'danger': C['danger']}
        icones = {'ok': '✓', 'info': 'ℹ', 'attention': '⚠', 'danger': '✗'}

        for type_c, msg in conseils:
            c = couleurs.get(type_c, C['text'])
            icon = icones.get(type_c, '•')
            tk.Label(frame, text=f"{icon} {msg}",
                     bg=C['surface'], fg=c, font=FONT_BODY,
                     wraplength=420, justify='left').pack(anchor='w', pady=4)

        tk.Button(self, text="Fermer", bg=C['accent'], fg='white',
                  font=FONT_BOLD, relief='flat', cursor='hand2',
                  padx=20, pady=8, activebackground='#c73652',
                  command=self.destroy).pack(pady=10)
