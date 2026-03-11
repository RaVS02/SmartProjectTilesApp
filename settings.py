# settings.py

# --- USTAWIENIA OKNA GŁÓWNEGO ---
WINDOW_TITLE = "Smart Project Tiles - Manager and Workflow"
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700

# --- PALETA KOLORÓW ---
# Format dla CustomTkinter: ("Kolor_Jasny_Motyw", "Kolor_Ciemny_Motyw")

PRIORITY_COLORS = {
    "very-high":("#ff4a4a", "#cc0000"),
    "high": ("#f2a829", "#c75e00"),
    "medium": ("#ffff00", "#f5ee00"),
    "low":("#00ff2a", "#00cc00"),
    "without":("#f0f0f0", "#2b2b2b")
}

# Domyślny kolor tła kafelka (gdy użytkownik nie wymusi własnego)
DEFAULT_TILE_COLOR = ("#f0f0f0", "#2b2b2b")
# Kolor dla kafelków oznaczonych jako Zrobione
COMPLETED_TILE_COLOR = ("#e0e0e0", "#1a1a1a")

# --- USTAWIENIA CZCIONEK ---
# Format: ("Nazwa czcionki", rozmiar, "styl")
FONT_TITLE = ("Helvetica", 16, "bold")
FONT_DEFAULT = ("Helvetica", 12)
FONT_TAGS = ("Helvetica", 10, "italic")

# --- LOGIKA PRIORYTETÓW (Sortowanie i Tekst) ---
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