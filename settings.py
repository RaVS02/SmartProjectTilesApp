# settings.py

# --- USTAWIENIA OKNA GŁÓWNEGO ---
WINDOW_TITLE = "Smart Project Tiles - Manager and Workflow"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

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
# --- LOGIKA CZASU I WAG SUMARYCZNYCH ---
# 7 przechodzących kolorów dla tekstów oznaczających czas
TIME_COLORS = {
    "overdue": ("#8b0000", "#ff4a4a"), # Czerwony (po terminie)
    "today":   ("#cc0000", "#ff3333"), # Jasnoczerwony (na dziś)
    "1_3":     ("#e65c00", "#ff7b00"), # Ciemnopomarańczowy (1-3 dni)
    "4_7":     ("#b38f00", "#ffcc00"), # Pomarańczowo-żółty (4-7 dni)
    "8_14":    ("#739900", "#99cc00"), # Żółto-zielony (8-14 dni)
    "15_plus": ("#2e8b57", "#3cb371"), # Zielony (+15 dni)
    "none":    ("#808080", "#a9a9a9")  # Szary (brak terminu)
}

# Gradient kolorów ramek dla wag sumarycznych (Priorytet 1-5 + Czas 1-6 = Wynik od 2 do 11)
SUMMATIVE_COLORS = {
    2: ("#ff0000", "#cc0000"), # Krytyczne
    3: ("#ff3300", "#cc2900"),
    4: ("#ff6600", "#cc5200"),
    5: ("#ff9900", "#cc7a00"),
    6: ("#ffcc00", "#cca300"),
    7: ("#ccff00", "#a3cc00"),
    8: ("#99ff00", "#7acc00"),
    9: ("#66ff00", "#52cc00"),
    10: ("#33ff00", "#29cc00"),
    11: ("#00ff00", "#00cc00") # Zupełnie na luzie
}
# --- NIESTANDARDOWE KOLORY KAFELKÓW (Z delikatną przezroczystością / Pastelowe) ---
# Format: "Nazwa": ("Kolor_Jasny_Motyw", "Kolor_Ciemny_Motyw")
CUSTOM_TILE_COLORS = {
    "Domyślny": None,
    "Błękitny (Delikatny)": ("#e6f0fa", "#1a2a3a"),
    "Miętowy (Delikatny)": ("#e6fae6", "#1a3a20"),
    "Różowy (Delikatny)": ("#fae6e6", "#3a1a1a"),
    "Lawendowy (Delikatny)": ("#f0e6fa", "#2a1a3a"),
    "Słoneczny (Delikatny)": ("#fafae6", "#3a3a1a"),
    "Brzoskwiniowy (Delikatny)": ("#faefe6", "#3a2a1a")
}