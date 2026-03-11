import customtkinter as ctk
import settings as st
from models import TileManager, ProjectTileModel
from ui import ProjectTileWidget, TileFormDialog

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("green")


import math # <--- Upewnij się, że masz to zaimportowane na górze pliku main.py

import math
import tkinter as tk  # Potrzebne do Canvasu


class WorkflowCanvasFrame(ctk.CTkFrame):
    """Płótno z paskiem narzędzi bocznych do tworzenia diagramów"""

    def __init__(self, master, tile_model, close_callback, manager, **kwargs):
        super().__init__(master, **kwargs)
        self.model = tile_model
        self.close_callback = close_callback
        self.manager = manager

        # Układ: 2 wiersze (header, canvas), 2 kolumny (toolbar, canvas)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)  # Kolumna 1 (płótno) zabiera całe wolne miejsce

        # ==========================================
        # 1. PASEK GÓRNY (Header)
        # ==========================================
        header = ctk.CTkFrame(self, height=50, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))

        ctk.CTkButton(header, text="< Wróć do listy", width=100, command=self.close_callback).pack(side="left",
                                                                                                   padx=(0, 20))
        ctk.CTkLabel(header, text=f"📍 Workflow: {self.model.title}", font=st.FONT_TITLE).pack(side="left")

        # Przyciski zarządzania płótnem
        ctk.CTkButton(header, text="💾 Zapisz", width=100, fg_color="green", hover_color="darkgreen",
                      command=self.save_workflow).pack(side="right", padx=(10, 0))
        ctk.CTkButton(header, text="🗑️ Wyczyść", width=100, fg_color="#8b0000", hover_color="#5c0000",
                      command=self.clear_canvas).pack(side="right")

        # ==========================================
        # 2. PASEK NARZĘDZI BOCZNY (Toolbar)
        # ==========================================
        self.toolbar = ctk.CTkFrame(self, width=160)
        self.toolbar.grid(row=1, column=0, sticky="ns", padx=(20, 10), pady=(0, 20))

        ctk.CTkLabel(self.toolbar, text="Narzędzia", font=st.FONT_TITLE).pack(pady=(15, 20))

        # Zmienna przechowująca aktualnie wybrany tryb narzędzia
        self.current_mode = tk.StringVar(value="move")

        # Lista dostępnych narzędzi (Tekst na przycisku, wartość trybu)
        tools = [
            ("🖱️ Przesuwaj / Edytuj", "move"),
            ("🔲 Dodaj Blok", "add_block"),
            ("📝 Dodaj Notatkę", "add_note"),
            ("↗️ Połącz (Strzałka)", "add_edge"),
            ("❌ Usuń element", "delete")
        ]

        # Generowanie przycisków Radio (tylko jeden może być wciśnięty)
        for text, mode in tools:
            rb = ctk.CTkRadioButton(
                self.toolbar,
                text=text,
                variable=self.current_mode,
                value=mode,
                font=("Helvetica", 13),
                command=self.on_tool_changed
            )
            rb.pack(anchor="w", padx=15, pady=12)

        # ==========================================
        # 3. OBSZAR PŁÓTNA (Canvas)
        # ==========================================
        self.canvas_container = ctk.CTkFrame(self)
        self.canvas_container.grid(row=1, column=1, sticky="nsew", padx=(0, 20), pady=(0, 20))

        # Używamy czystego tkinter Canvas, bo CustomTkinter nie ma natywnego rysowania linii
        self.canvas = tk.Canvas(self.canvas_container, bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=2, pady=2)

        # PODPIĘCIE GŁÓWNYCH ZDARZEŃ MYSZY (Fundamenty pod kolejny krok)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    # --- FUNKCJE INTERFEJSU PŁÓTNA ---
    def on_tool_changed(self):
        """Zmienia kursor myszy w zależności od narzędzia, żeby użytkownik wiedział w jakim jest trybie"""
        mode = self.current_mode.get()
        if mode == "add_edge":
            self.canvas.configure(cursor="crosshair")  # Celownik
        elif mode == "delete":
            self.canvas.configure(cursor="pirate")  # Czaszka/krzyżyk (w zależności od systemu)
        elif mode in ["add_block", "add_note"]:
            self.canvas.configure(cursor="plus")  # Plusik
        else:
            self.canvas.configure(cursor="arrow")  # Zwykły kursor

    def on_canvas_click(self, event):
        """Złapie kliknięcie na płótnie i sprawdzi, jakie narzędzie jest aktywne"""
        mode = self.current_mode.get()
        print(f"DEBUG: Kliknięto w X:{event.x}, Y:{event.y} | Aktywny tryb: {mode}")

        # Tutaj w kolejnym kroku dodamy logikę tworzenia bloków!

    def save_workflow(self):
        """Zapisuje cały stan na dysk"""
        # Tu w przyszłości dodamy pakowanie narysowanych elementów do self.model.workflow_data
        self.manager.save_to_file()
        print("DEBUG: Zapisano zmiany workflow na dysku.")

    def clear_canvas(self):
        """Czyści ekran roboczy"""
        self.canvas.delete("all")
        print("DEBUG: Wyczyściliśmy płótno.")

class SmartProjectTilesApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(st.WINDOW_TITLE)
        self.geometry(f"{st.WINDOW_WIDTH}x{st.WINDOW_HEIGHT}")

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self.current_page = 1
        self.items_per_page = 15
        self.search_timer = None

        # NOWE: Zmienne do łapania rozmiaru okna
        self.resize_timer = None
        self.last_width = st.WINDOW_WIDTH

        self.setup_ui()

        # Nasłuchiwanie zmiany rozmiaru GŁÓWNEGO okna
        self.bind("<Configure>", self.on_window_resize)



    def setup_ui(self):
        self.manager = TileManager()
        self.manager.load_from_file()

        # Ustawiamy motyw zaraz po wczytaniu preferencji
        self.change_theme(self.manager.preferences.get("theme", "System"), save=False)

        # ==========================================
        # 1. PASEK NARZĘDZI (Wiersz 0)
        # ==========================================
        self.toolbar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        self.toolbar_frame.grid_columnconfigure(1, weight=1)

        self.add_btn = ctk.CTkButton(self.toolbar_frame, text="+ Dodaj Kafelek", font=st.FONT_TITLE,
                                     command=self.open_add_dialog)
        self.add_btn.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(self.toolbar_frame, text="Rozmiar:").grid(row=0, column=1, sticky="e", padx=(0, 10))
        self.mode_var = ctk.StringVar(value=self.manager.preferences.get("mode", "Pełny"))
        self.mode_switcher = ctk.CTkSegmentedButton(self.toolbar_frame, values=["Pełny", "Skrócony"],
                                                    variable=self.mode_var, command=self.on_preference_change)
        self.mode_switcher.grid(row=0, column=2, sticky="e", padx=(0, 20))

        ctk.CTkLabel(self.toolbar_frame, text="Kolumny:").grid(row=0, column=3, sticky="e", padx=(0, 10))
        self.col_var = ctk.StringVar(value=self.manager.preferences.get("columns", "3"))
        self.col_switcher = ctk.CTkSegmentedButton(self.toolbar_frame, values=["1", "2", "3", "4", "5"],
                                                   variable=self.col_var, command=self.on_preference_change)
        self.col_switcher.grid(row=0, column=4, sticky="e", padx=(0, 20))

        ctk.CTkLabel(self.toolbar_frame, text="Motyw:").grid(row=0, column=5, sticky="e", padx=(0, 10))
        self.theme_var = ctk.StringVar(value=self.manager.preferences.get("theme", "System"))
        self.theme_switcher = ctk.CTkSegmentedButton(self.toolbar_frame, values=["Jasny", "Ciemny", "System"],
                                                     variable=self.theme_var, command=self.change_theme)
        self.theme_switcher.grid(row=0, column=6, sticky="e")

        # ==========================================
        # 2. PASEK FILTRÓW I SORTOWANIA (Wiersz 1)
        # ==========================================
        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 0))
        self.filter_frame.grid_columnconfigure(0, weight=1)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.schedule_search)

        self.search_entry = ctk.CTkEntry(self.filter_frame, textvariable=self.search_var,
                                         placeholder_text="🔍 Szukaj po nazwie lub tagu...", width=250)
        self.search_entry.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(self.filter_frame, text="Kolory:").grid(row=0, column=1, sticky="e", padx=(0, 10))
        self.color_style_var = ctk.StringVar(value=self.manager.preferences.get("color_style", "Kolorowe Tło"))
        self.color_style_menu = ctk.CTkOptionMenu(
            self.filter_frame, values=["Kolorowe Tło", "Tylko Ramki", "Minimalistyczny"],
            variable=self.color_style_var, command=self.on_preference_change, width=130
        )
        self.color_style_menu.grid(row=0, column=2, sticky="e", padx=(0, 20))

        ctk.CTkLabel(self.filter_frame, text="Sortuj:").grid(row=0, column=3, sticky="e", padx=(0, 10))
        self.sort_var = ctk.StringVar(value=self.manager.preferences.get("sort_by", "Waga Sumaryczna"))
        self.sort_menu = ctk.CTkOptionMenu(
            self.filter_frame, values=["Waga Sumaryczna", "Deadline", "Główny Priorytet", "Nazwa (A-Z)", "Tagi (A-Z)"],
            variable=self.sort_var, command=self.on_preference_change, width=160
        )
        self.sort_menu.grid(row=0, column=4, sticky="e")

        self.sort_order_var = ctk.StringVar(value=self.manager.preferences.get("sort_order", "Rosnąco"))
        self.sort_order_btn = ctk.CTkButton(self.filter_frame, textvariable=self.sort_order_var, width=70,
                                            command=self.toggle_sort_order)
        self.sort_order_btn.grid(row=0, column=5, sticky="e", padx=(10, 0))

        # ==========================================
        # 3. RAMKA KAFELKÓW (Wiersz 2) & 4. STRONICOWANIE (Wiersz 3)
        # ==========================================
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 10))

        self.pagination_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.pagination_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 15))
        self.pagination_frame.grid_columnconfigure(1, weight=1)

        self.prev_btn = ctk.CTkButton(self.pagination_frame, text="< Poprzednia", width=100, command=self.prev_page)
        self.prev_btn.grid(row=0, column=0, sticky="w")
        self.page_label = ctk.CTkLabel(self.pagination_frame, text="Strona 1 z 1", font=st.FONT_DEFAULT)
        self.page_label.grid(row=0, column=1, sticky="ew")
        self.next_btn = ctk.CTkButton(self.pagination_frame, text="Następna >", width=100, command=self.next_page)
        self.next_btn.grid(row=0, column=2, sticky="e")

        self.draw_tiles()

    # --- NOWA FUNKCJA: DEBOUNCING ---
    def on_window_resize(self, event):
        """Opóźnione przerysowanie kafelków po zmianie szerokości głównego okna"""
        if event.widget == self:
            current_width = self.winfo_width()
            # Przerysowujemy tylko, gdy rozmiar zmienił się o co najmniej 50px (zero niepotrzebnego migotania)
            if abs(current_width - self.last_width) > 50:
                self.last_width = current_width
                if self.resize_timer:
                    self.after_cancel(self.resize_timer)
                self.resize_timer = self.after(100, lambda: self.draw_tiles(reset_page=False))

    def schedule_search(self, *args):
        if self.search_timer: self.after_cancel(self.search_timer)
        self.search_timer = self.after(300, lambda: self.draw_tiles(reset_page=True))

    def save_current_preferences(self):
        """Aktualizuje słownik w menedżerze i zapisuje go do JSONa"""
        self.manager.preferences["mode"] = self.mode_var.get()
        self.manager.preferences["columns"] = self.col_var.get()
        self.manager.preferences["theme"] = self.theme_var.get()
        self.manager.preferences["color_style"] = self.color_style_var.get()
        self.manager.preferences["sort_by"] = self.sort_var.get()
        self.manager.preferences["sort_order"] = self.sort_order_var.get()
        self.manager.save_to_file()

    def on_preference_change(self, *args):
        """Wywoływana przy kliknięciu w filtry/widoki - zapisuje stan i odświeża ekran"""
        self.save_current_preferences()
        self.draw_tiles()
    def change_theme(self, theme_name, save=True):
        if theme_name == "Jasny":
            ctk.set_appearance_mode("Light")
        elif theme_name == "Ciemny":
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("System")

        if save:
            self.save_current_preferences()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.draw_tiles(reset_page=False)

    def next_page(self):
        self.current_page += 1
        self.draw_tiles(reset_page=False)

    def toggle_sort_order(self):
        current = self.sort_order_var.get()
        self.sort_order_var.set("Malejąco" if current == "Rosnąco" else "Rosnąco")
        self.on_preference_change()

    def open_add_dialog(self):
        dialog = TileFormDialog(master=self, on_save_callback=self.save_new_tile)

    def save_new_tile(self, new_tile_model):
        self.manager.add_tile(new_tile_model)
        self.manager.save_to_file()
        self.draw_tiles(reset_page=True)

    def draw_tiles(self, reset_page=True):
        if reset_page:
            self.current_page = 1

        columns = int(self.col_var.get())
        is_compact = (self.mode_var.get() == "Skrócony")
        color_style = self.color_style_var.get()

        for widget in self.scrollable_frame.winfo_children(): widget.destroy()

        for i in range(10): self.scrollable_frame.grid_columnconfigure(i, weight=0)
        for i in range(columns): self.scrollable_frame.grid_columnconfigure(i, weight=1)

        query = self.search_var.get().lower().strip()
        filtered_tiles = [t for t in self.manager.tiles if
                          query in t.title.lower() or any(query in tag.lower() for tag in t.tags)]

        sort_mode = self.sort_var.get()
        is_descending = self.sort_order_var.get() == "Malejąco"

        if sort_mode == "Waga Sumaryczna":
            filtered_tiles.sort(key=lambda x: x.total_weight, reverse=is_descending)
        elif sort_mode == "Deadline":
            filtered_tiles.sort(
                key=lambda x: x.days_left if x.days_left is not None else (9999 if not is_descending else -9999),
                reverse=is_descending)
        elif sort_mode == "Główny Priorytet":
            filtered_tiles.sort(key=lambda x: st.PRIORITY_RANK.get(x.priority, 5), reverse=is_descending)
        elif sort_mode == "Nazwa (A-Z)":
            filtered_tiles.sort(key=lambda x: x.title.lower(), reverse=is_descending)
        elif sort_mode == "Tagi (A-Z)":
            filtered_tiles.sort(key=lambda x: x.tags[0].lower() if x.tags else "zzz", reverse=is_descending)

        filtered_tiles.sort(key=lambda x: x.is_pinned, reverse=True)
        filtered_tiles.sort(key=lambda x: x.is_completed, reverse=False)

        total_pages = max(1, math.ceil(len(filtered_tiles) / self.items_per_page))
        if self.current_page > total_pages:
            self.current_page = total_pages

        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        limited_tiles = filtered_tiles[start_idx:end_idx]

        self.page_label.configure(text=f"Strona {self.current_page} z {total_pages}")
        self.prev_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < total_pages else "disabled")

        # ==========================================
        # NOWE: MATEMATYKA SZEROKOŚCI KAFELKA
        # ==========================================
        # Pobieramy obecną szerokość okna (lub startową z settings)
        app_width = self.winfo_width()

        # POPRAWKA 1: Zwiększamy próg do 250px. Przy starcie okno czasem zgłasza np. 200px
        # zanim Windows/Mac zdąży je rozciągnąć.
        if app_width < 250:
            app_width = st.WINDOW_WIDTH

        # Odejmujemy marginesy boczne głównego okna i pasek przewijania (~80px)
        estimated_tile_width = (app_width - 80) / columns

        # POPRAWKA 2: Zwiększamy margines z 130 na 160 pikseli, żeby dać tytułowi
        # i ikonom po prawej stronie (pinezka, priorytet) więcej "oddechu".
        calculated_wrap = max(50, int(estimated_tile_width - 160))

        # ==========================================
        # RYSOWANIE GOTOWYCH KAFELKÓW
        # ==========================================
        for index, tile_model in enumerate(limited_tiles):
            wiersz = index // columns
            kolumna = index % columns

            tile_widget = ProjectTileWidget(
                master=self.scrollable_frame,
                tile_model=tile_model,
                is_compact=is_compact,
                color_style=color_style,
                title_wrap=calculated_wrap,  # <--- Wstrzykujemy "sztywne ramy" prosto z Twojego pomysłu!
                save_callback=self.manager.save_to_file,
                delete_callback=self.delete_tile,
                complete_callback=self.complete_tile,
                edit_callback=self.edit_tile,
                restore_callback=self.restore_tile,
                pin_callback=self.pin_tile,
                open_workflow_callback = self.open_workflow_view
            )
            tile_widget.grid(row=wiersz, column=kolumna, padx=10, pady=10, sticky="nsew")

    def pin_tile(self, tile_model):
        tile_model.is_pinned = not tile_model.is_pinned
        self.manager.save_to_file()
        self.draw_tiles(reset_page=False)

    def restore_tile(self, tile_model):
        tile_model.is_completed = False
        self.manager.save_to_file()
        self.draw_tiles(reset_page=False)

    def delete_tile(self, tile_model):
        self.manager.tiles.remove(tile_model)
        self.manager.save_to_file()
        self.draw_tiles(reset_page=False)

    def complete_tile(self, tile_model):
        tile_model.is_completed = True
        tile_model.is_pinned = False
        self.manager.save_to_file()
        self.draw_tiles(reset_page=False)

    def edit_tile(self, tile_model):
        dialog = TileFormDialog(master=self, on_save_callback=self.update_existing_tile, existing_tile=tile_model)

    def update_existing_tile(self, updated_model):
        self.manager.save_to_file()
        self.draw_tiles(reset_page=False)

    def open_workflow_view(self, tile_model):
        """Ukrywa główny widok i otwiera płótno dla konkretnego kafelka"""
        # 1. Chowamy (ale nie niszczymy!) główne elementy GUI
        self.toolbar_frame.grid_remove()
        self.filter_frame.grid_remove()
        self.scrollable_frame.grid_remove()
        self.pagination_frame.grid_remove()

        # 2. Tworzymy nowy widok Workflow i każemy mu wypełnić całe okno (rowspan=4)
        self.workflow_view = WorkflowCanvasFrame(
            master=self,
            tile_model=tile_model,
            close_callback=self.close_workflow_view,
            manager=self.manager
        )
        self.workflow_view.grid(row=0, column=0, rowspan=4, sticky="nsew")

    def close_workflow_view(self):
        """Niszczy płótno i przywraca główny widok"""
        self.workflow_view.destroy()

        # Przywracamy schowane elementy GUI
        self.toolbar_frame.grid()
        self.filter_frame.grid()
        self.scrollable_frame.grid()
        self.pagination_frame.grid()

        # Przerenderowujemy kafelki (na wypadek gdyby nazwa projektu się zmieniła w workflow)
        self.draw_tiles(reset_page=False)

if __name__ == "__main__":
    app = SmartProjectTilesApp()
    app.mainloop()