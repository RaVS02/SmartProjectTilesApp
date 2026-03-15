# settings.py

# ==========================================
# 1. USTAWIENIA OKNA GŁÓWNEGO
# ==========================================
WINDOW_TITLE = "Smart Project Tiles - Manager and Workflow"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

# ==========================================
# 2. LOGIKA PRIORYTETÓW
# ==========================================
PRIORITY_RANK = {
    "very-high": 1,
    "high": 2,
    "medium": 3,
    "low": 4,
    "without": 5
}

PRIORITY_LABELS = {
    "very-high": "Bardzo wysoki",
    "high": "Wysoki",
    "medium": "Średni",
    "low": "Niski",
    "without": "Brak"
}

PRIORITY_COLORS = {
    "very-high": ("#ff4a4a", "#cc0000"),
    "high": ("#f2a829", "#c75e00"),
    "medium": ("#ffff00", "#f5ee00"),
    "low": ("#00ff2a", "#00cc00"),
    "without": ("#f0f0f0", "#2b2b2b")
}

# ==========================================
# 3. LOGIKA CZASU I WAG SUMARYCZNYCH
# ==========================================
TIME_COLORS = {
    "overdue": ("#8b0000", "#ff4a4a"),
    "today":   ("#cc0000", "#ff3333"),
    "1_3":     ("#e65c00", "#ff7b00"),
    "4_7":     ("#b38f00", "#ffcc00"),
    "8_14":    ("#739900", "#99cc00"),
    "15_plus": ("#2e8b57", "#3cb371"),
    "none":    ("#808080", "#a9a9a9")
}

SUMMATIVE_COLORS = {
    2: ("#ff0000", "#cc0000"),
    3: ("#ff3300", "#cc2900"),
    4: ("#ff6600", "#cc5200"),
    5: ("#ff9900", "#cc7a00"),
    6: ("#ffcc00", "#cca300"),
    7: ("#ccff00", "#a3cc00"),
    8: ("#99ff00", "#7acc00"),
    9: ("#66ff00", "#52cc00"),
    10: ("#33ff00", "#29cc00"),
    11: ("#00ff00", "#00cc00")
}

# ==========================================
# 4. GŁÓWNA PALETA KOLORÓW (KAFELKI)
# ==========================================
DEFAULT_TILE_COLOR = ("#f0f0f0", "#2b2b2b")
COMPLETED_TILE_COLOR = ("#e0e0e0", "#1a1a1a")

CUSTOM_TILE_COLORS = {
    "Domyślny": None,
    "Błękitny (Delikatny)": ("#e6f0fa", "#1a2a3a"),
    "Miętowy (Delikatny)": ("#e6fae6", "#1a3a20"),
    "Różowy (Delikatny)": ("#fae6e6", "#3a1a1a"),
    "Lawendowy (Delikatny)": ("#f0e6fa", "#2a1a3a"),
    "Słoneczny (Delikatny)": ("#fafae6", "#3a3a1a"),
    "Brzoskwiniowy (Delikatny)": ("#faefe6", "#3a2a1a"),
    "Morski (Wyrazisty)": ("#b3e0ff", "#004d80"),
    "Szmaragdowy (Wyrazisty)": ("#b3ffcc", "#006622"),
    "Koralowy (Wyrazisty)": ("#ffb3b3", "#800000"),
    "Fiołkowy (Wyrazisty)": ("#d9b3ff", "#4d0080"),
    "Złoty (Wyrazisty)": ("#ffe6b3", "#806600")
}

# ==========================================
# 5. USTAWIENIA CZCIONEK (GŁÓWNE UI)
# ==========================================
FONT_TITLE = ("Helvetica", 16, "bold")
FONT_DEFAULT = ("Helvetica", 12)
FONT_TAGS = ("Helvetica", 10, "italic")

# ==========================================
# 6. KONFIGURACJA PŁÓTNA (WORKFLOW CANVAS)
# ==========================================
WORKFLOW_BG_COLORS = {
    "Ciemne": "#1a1a1a",
    "Białe": "#ffffff",
    "Szare": "#2b2b2b",
    "Niebieskie": "#1e293b",
    "Czarne": "#000000"
}

NODE_TYPES = {
    "Kafelek Projektu (Szczegółowy)": "project",
    "Zwykły Blok": "block",
    "Notatka": "note",
    "Tylko Tekst (Etykieta)": "text"
}

NODE_SHAPES = {
    "Prostokąt zaokrąglony (Proces)": "rect",
    "Kapsuła (Start/Koniec)": "capsule",
    "Romb (Decyzja)": "diamond",
    "Elipsa (Zdarzenie)": "oval",
    "Równoległobok (Wejście/Wyjście)": "parallelogram",
    "Sześciokąt (Przygotowanie)": "hexagon",
    "Trapez (Ręczne wprowadzanie)": "trapezoid"
}

NODE_BG_COLORS = {
    "Domyślny": None,
    "Ciemnoszary": "#2b2b2b",
    "Jasnoszary": "#4a4a4a",
    "Kremowy (Notatka)": "#e6c280",
    "Brązowy (Notatka)": "#b35900"
}
for k, v in CUSTOM_TILE_COLORS.items():
    if k != "Domyślny" and v:
        NODE_BG_COLORS[k] = v[1] if isinstance(v, tuple) else v

NODE_BORDER_COLORS = {
    "Domyślny Szary": "#666666",
    "Czerwony (Krytyczny)": PRIORITY_COLORS["very-high"][1],
    "Pomarańczowy (Wysoki)": PRIORITY_COLORS["high"][1],
    "Żółty (Średni)": PRIORITY_COLORS["medium"][1],
    "Zielony (Niski)": PRIORITY_COLORS["low"][1],
    "Fioletowy": "#4b0082",
    "Biały": "#ffffff",
    "Czarny": "#000000"
}
# ZMIANA: Dodano bogatą paletę kolorów również do ramek
for k, v in CUSTOM_TILE_COLORS.items():
    if k != "Domyślny" and v:
        NODE_BORDER_COLORS[k] = v[1] if isinstance(v, tuple) else v

CANVAS_FONT_FAMILIES = ["Helvetica", "Arial", "Times New Roman", "Courier New", "Verdana", "Impact"]
CANVAS_FONT_SIZES = ["8", "10", "12", "14", "16", "20", "24", "32", "48"]

CANVAS_FONT_COLORS = {
    "Domyślny": None,
    "Czarny": "#000000",
    "Biały": "#ffffff",
    "Jasnoszary": "#cccccc",
    "Czerwony": "#ff4a4a",
    "Pomarańczowy": "#ff9900",
    "Żółty": "#ffcc00",
    "Zielony": "#00cc00",
    "Morski": "#00ffcc",
    "Niebieski": "#4da6ff",
    "Fioletowy": "#cc66ff",
    "Różowy": "#ff99cc"
}

EDGE_DIRECTIONS = {
    "A ➔ B (Domyślny)": "last",
    "A ⬅ B (Odwrotny)": "first",
    "A ⬌ B (Dwukierunkowy)": "both",
    "Linia zwykła (Brak)": "none"
}

EDGE_COLORS = {
    "Szary (Domyślny)": "#888888",
    "Czerwony (Błąd/Nie)": "#ff4a4a",
    "Zielony (Sukces/Tak)": "#00cc00",
    "Niebieski (Informacja)": "#2980b9",
    "Pomarańczowy": "#ff9900",
    "Fioletowy": "#cc66ff",
    "Morski": "#00ffcc"
}

EDGE_WIDTHS = ["1", "2", "3", "4", "5"]

# ==========================================
# 7. KOLORY ELEMENTÓW UI
# ==========================================
PROGRESS_BAR_COLORS = {
    0: "#cc0000",
    25: "#cc6600",
    50: "#e6b800",
    75: "#99cc00",
    100: "#00cc00"
}
ARCHIVED_TILE_BG = ("#2b2b2b", "#1a1a1a")
ARCHIVED_TILE_BORDER = "#444444"
PIN_ACTIVE = ("#c29200", "#ffcc00")
PIN_INACTIVE = ("#999999", "#666666")
PIN_HOVER = ("#e0e0e0", "#3a3a3a")

BTN_WORKFLOW = {"fg": "#1f538d", "hover": "#14375e"}
BTN_RESTORE = {"fg": "#d48806", "hover": "#b07004"}
BTN_DONE = {"fg": "green", "hover": "darkgreen"}
BTN_DELETE = {"fg": "#8b0000", "hover": "#5c0000"}