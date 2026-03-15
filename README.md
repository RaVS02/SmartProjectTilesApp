# 🚀 Smart Project Tiles 

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-green.svg)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-darkblue.svg)

**Smart Project Tiles** to zaawansowane, desktopowe środowisko do zarządzania projektami i produktywnością, zbudowane w architekturze **MVC**. Omija ograniczenia standardowych list "To-Do", łącząc w sobie analityczny dashboard, interaktywny kalendarz oraz potężny, natywny silnik diagramów przepływu (Infinite Canvas).

---

## 📖 Spis Treści
- [Architektura Systemu](#-architektura-systemu)
- [Kluczowe Moduły (Features)](#-kluczowe-moduły)
- [Silnik Graficzny Workflow](#-silnik-graficzny-workflow)
- [Struktura Katalogów](#-struktura-katalogów)
- [Kompilacja i Wdrożenie](#-kompilacja-i-wdrożenie)

---

## 🏗️ Architektura Systemu

Aplikacja została zaprojektowana z myślą o skalowalności, pełnej modularności oraz separacji warstwy logiki od warstwy prezentacji. 

* **State Management (Zarządzanie Stanem):** Cały stan aplikacji (kafelki, preferencje UI, język, układ kolumn) jest przechowywany w globalnym obiekcie `TileManager` i serializowany do pliku `data.json`.
* **Single Source of Truth:** `settings.py` działa jako scentralizowany magazyn konfiguracji. Zmiana palety kolorów kafelka, modyfikacja promienia zaokrąglenia figur geometrycznych czy dodanie nowego typu priorytetu nie wymaga ingerencji w kod widoków.
* **i18n (Internationalization):** Autorski silnik tłumaczeń (`translations.py`) z mechanizmem *Reverse Translation* (`rev_tr`), pozwalający na zmianę języka UI w czasie rzeczywistym bez restartu maszyny, zachowując przy tym spójność identyfikatorów w bazie danych.

---

## ✨ Kluczowe Moduły

### 1. Tablica Kafelków (Smart Board)
Sercem systemu jest dynamiczny Grid. Kafelki to nie tylko pojemniki na tekst – to modele obliczeniowe.
* **Matematyczna "Waga":** Aplikacja automatycznie nadaje priorytety wizualne na podstawie rangi projektu i czasu pozostałego do deadline'u.
* **Listy zadań:** Dynamiczne parsowanie zawartości i generowanie wskaźników postępu.

### 2. Kalendarz Drag & Drop
* Integracja z autorskim systemem **Drop Zones**. 
* Użytkownik może pobierać nieprzypisane zadania z "Poczekalni" i przeciągać je na siatkę kalendarza. Przechwycenie zdarzenia `<ButtonRelease>` automatycznie przelicza koordynaty, aktualizuje daty w obiekcie modelu i wymusza re-render widoku.

### 3. Moduł Analityczny (Dashboard)
* Iteruje po wszystkich dostępnych projektach w pamięci i w czasie rzeczywistym generuje **wskaźniki KPI**.
* Wykorzystuje customowe widgety pasków postępu do wizualizacji tzw. *Global Task Progress* (ile ogólnie zadań wykonano we wszystkich projektach) oraz rozkładu priorytetów.

---

## 🗺️ Silnik Graficzny Workflow (Płótno)

Najbardziej złożony technicznie moduł w aplikacji. Oparty na niskopoziomowym manipulowaniu obiektem `tk.Canvas`.

* **Customowe Kształty (Polygon Rendering):** Własne procedury matematyczne do rysowania m.in. rombów, sześciokątów czy trapezów.
* **Smart Bounding Boxes:** Dynamiczne obliczanie przestrzeni dla tekstu. Tekst, który nie mieści się wewnątrz figury przy skalowaniu, jest matematycznie obcinany (Trimming z wielokropkiem), co zapobiega wychodzeniu renderowanego napisu poza krawędzie bloku.
* **Polygon Clipping:** Precyzyjne odcinanie górnej połowy dowolnego wielokąta w celu zastosowania filtru ściemniającego (`darken_hex`) dla nagłówków.
* **Zaawansowana Interakcja:** * Skalowanie proporcjonalne z użyciem klawisza `SHIFT`.
  * Zaznaczanie grupowe (Lasso Tool).
  * System *Undo/Redo* oparty na stosie historii stanów (History Stack).

---

## 📂 Struktura Katalogów

```text
SmartProjectTiles/
│
├── main.py                # Główny kontroler okna (Routing, Filtry, Paginacja)
├── models.py              # Klasy danych (ProjectTileModel, TileManager)
├── settings.py            # Konfiguracja UI/UX (Palety, Kształty, Marginesy)
├── translations.py        # Silnik wielojęzyczności i słowniki (PL/EN)
├── ui.py                  # Definicja widżetu pojedynczego Kafelka
├── ui_calendar.py         # Logika widoku Kalendarza i systemu Drag & Drop
├── ui_dialogs.py          # Okna Modalne (Formularze, Edytory Właściwości)
├── ui_statistics.py       # Generator widoku Dashboardu KPI
├── ui_workflow.py         # Silnik graficzny Canvas (Węzły, Krawędzie, Zoom)
├── ikona.ico              # Ikona aplikacji
└── data.json              # [Generowany automatycznie] Baza danych

Gotowy program znajdzie się w wygenerowanym folderze `dist/`. Wystarczy przenieść go w dowolne miejsce w systemie. Aplikacja automatycznie utworzy obok siebie plik `data.json` po pierwszym uruchomieniu.
```
---

## ⚖️ Licencja

Ten projekt jest udostępniany na licencji **GNU GPLv3**. Oznacza to, że możesz swobodnie pobierać, modyfikować i używać tego kodu do własnych celów. Jeśli jednak zdecydujesz się udostępnić zmodyfikowaną wersję tego programu, masz prawny obowiązek udostępnić jej kod źródłowy na tej samej, darmowej licencji. Szczegóły znajdziesz w pliku `LICENSE`.

---

## ☕ Wsparcie Projektu

Aplikacja została stworzona po godzinach, z ogromnej pasji do programowania i architektury oprogramowania. Jeśli ten projekt ułatwił Ci zarządzanie zadaniami, pomógł w nauce Pythona lub po prostu Ci się podoba – możesz postawić mi wirtualną kawę! Każde wsparcie to ogromna motywacja do dalszego kodowania. ❤️

[![Buy Me A Coffee](https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png)](https://www.buymeacoffee.com/sobalarafaa)

---

## 📜 Podziękowania (Credits)

Ikona aplikacji została stworzona przez **[Those Icons](https://icon-icons.com)** i pobrana z serwisu **[ICON-ICONS](https://icon-icons.com)**.
```
## 📜 Podziękowania (Credits)

Ikona aplikacji została stworzona przez **[Those Icons](https://thoseicons.com)** i pobrana z serwisu **[ICON-ICONS](https://icon-icons.com)**.`
