import customtkinter as ctk
import settings as st
import math
from models import TileManager
from ui import ProjectTileWidget
from ui_dialogs import TileFormDialog
from ui_workflow import WorkflowCanvasFrame
from ui_calendar import CalendarView

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("green")


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

        self.resize_timer = None
        self.last_width = st.WINDOW_WIDTH

        self.manager = TileManager()
        self.manager.load_from_file()

        self.setup_ui()
        self.bind("<Configure>", self.on_window_resize)

    def setup_ui(self):
        self.change_theme(self.manager.preferences.get("theme", "System"), save=False)

        # 1. PASEK NARZĘDZI (Wiersz 0)
        self.toolbar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        self.toolbar_frame.grid_columnconfigure(2, weight=1)

        self.add_btn = ctk.CTkButton(self.toolbar_frame, text="+ Dodaj Kafelek", font=st.FONT_TITLE,
                                     command=self.open_add_dialog)
        self.add_btn.grid(row=0, column=0, sticky="w")

        self.main_view_var = ctk.StringVar(value="Tablica")
        self.main_view_switcher = ctk.CTkSegmentedButton(self.toolbar_frame, values=["Tablica", "Kalendarz"],
                                                         variable=self.main_view_var, command=self.switch_main_view,
                                                         font=("Helvetica", 14, "bold"))
        self.main_view_switcher.grid(row=0, column=1, sticky="w", padx=(20, 0))

        ctk.CTkLabel(self.toolbar_frame, text="Rozmiar:").grid(row=0, column=2, sticky="e", padx=(0, 10))
        self.mode_var = ctk.StringVar(value=self.manager.preferences.get("mode", "Pełny"))
        self.mode_switcher = ctk.CTkSegmentedButton(self.toolbar_frame, values=["Pełny", "Skrócony"],
                                                    variable=self.mode_var, command=self.on_preference_change)
        self.mode_switcher.grid(row=0, column=3, sticky="e", padx=(0, 20))

        # --- DYNAMICZNE ELEMENTY (KOLUMNY vs KOLORY) ---
        # Kolumny (Domyślnie widoczne w Tablicy)
        self.col_lbl = ctk.CTkLabel(self.toolbar_frame, text="Kolumny:")
        self.col_lbl.grid(row=0, column=4, sticky="e", padx=(0, 10))
        self.col_var = ctk.StringVar(value=self.manager.preferences.get("columns", "3"))
        self.col_switcher = ctk.CTkSegmentedButton(self.toolbar_frame, values=["1", "2", "3", "4", "5"],
                                                   variable=self.col_var, command=self.on_preference_change)
        self.col_switcher.grid(row=0, column=5, sticky="e", padx=(0, 20))

        # Wspólna zmienna dla kolorów (podpięta też w filtrach Tablicy)
        self.color_style_var = ctk.StringVar(value=self.manager.preferences.get("color_style", "Kolorowe Tło"))

        # Kolory dla paska (Widoczne tylko w Kalendarzu!)
        self.cal_color_lbl = ctk.CTkLabel(self.toolbar_frame, text="Kolory:")
        self.cal_color_switcher = ctk.CTkOptionMenu(self.toolbar_frame,
                                                    values=["Kolorowe Tło", "Tylko Ramki", "Minimalistyczny"],
                                                    variable=self.color_style_var, command=self.on_preference_change,
                                                    width=130)

        ctk.CTkLabel(self.toolbar_frame, text="Motyw:").grid(row=0, column=6, sticky="e", padx=(0, 10))
        self.theme_var = ctk.StringVar(value=self.manager.preferences.get("theme", "System"))
        self.theme_switcher = ctk.CTkSegmentedButton(self.toolbar_frame, values=["Jasny", "Ciemny", "System"],
                                                     variable=self.theme_var, command=self.change_theme)
        self.theme_switcher.grid(row=0, column=7, sticky="e")
        # Przycisk pomocy na głównej belce
        self.help_btn = ctk.CTkButton(self.toolbar_frame, text="❓", width=30, command=self.show_main_help,
                                      fg_color="#1f538d")
        self.help_btn.grid(row=0, column=8, sticky="e", padx=(10, 0))
        # 2. PASEK FILTRÓW (Wiersz 1) - Tablica
        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 0))

        row1 = ctk.CTkFrame(self.filter_frame, fg_color="transparent")
        row1.pack(fill="x", pady=2)
        row1.grid_columnconfigure(0, weight=1)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.schedule_search)
        self.search_entry = ctk.CTkEntry(row1, textvariable=self.search_var,
                                         placeholder_text="🔍 Szukaj po nazwie lub tagu...", width=250)
        self.search_entry.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(row1, text="Kolory:").grid(row=0, column=1, sticky="e", padx=(0, 10))
        ctk.CTkOptionMenu(row1, values=["Kolorowe Tło", "Tylko Ramki", "Minimalistyczny"],
                          variable=self.color_style_var, command=self.on_preference_change, width=130).grid(row=0,
                                                                                                            column=2,
                                                                                                            sticky="e",
                                                                                                            padx=(0,
                                                                                                                  20))

        ctk.CTkLabel(row1, text="Sortuj:").grid(row=0, column=3, sticky="e", padx=(0, 10))
        self.sort_var = ctk.StringVar(value=self.manager.preferences.get("sort_by", "Waga Sumaryczna"))
        ctk.CTkOptionMenu(row1, values=["Waga Sumaryczna", "Deadline", "Główny Priorytet", "Nazwa (A-Z)", "Tagi (A-Z)"],
                          variable=self.sort_var, command=self.on_preference_change, width=160).grid(row=0, column=4,
                                                                                                     sticky="e")

        self.sort_order_var = ctk.StringVar(value=self.manager.preferences.get("sort_order", "Rosnąco"))
        ctk.CTkButton(row1, textvariable=self.sort_order_var, width=70, command=self.toggle_sort_order).grid(row=0,
                                                                                                             column=5,
                                                                                                             sticky="e",
                                                                                                             padx=(10,
                                                                                                                   0))

        row2 = ctk.CTkFrame(self.filter_frame, fg_color="transparent")
        row2.pack(fill="x", pady=5)

        ctk.CTkLabel(row2, text="Status:").pack(side="left", padx=(0, 5))
        self.filter_status_var = ctk.StringVar(value=self.manager.preferences.get("filter_status", "Wszystkie"))
        ctk.CTkOptionMenu(row2, values=["Wszystkie", "Tylko Aktywne", "Tylko Ukończone"],
                          variable=self.filter_status_var, command=self.on_preference_change, width=130).pack(
            side="left", padx=(0, 20))

        ctk.CTkLabel(row2, text="Workflow:").pack(side="left", padx=(0, 5))
        self.filter_wf_var = ctk.StringVar(value=self.manager.preferences.get("filter_wf", "Wszystkie"))
        ctk.CTkOptionMenu(row2, values=["Wszystkie", "Z Workflow", "Bez Workflow"], variable=self.filter_wf_var,
                          command=self.on_preference_change, width=130).pack(side="left", padx=(0, 20))

        self.filter_no_deadline_var = ctk.BooleanVar(value=self.manager.preferences.get("filter_no_deadline", False))
        ctk.CTkCheckBox(row2, text="Ukryj bez terminu", variable=self.filter_no_deadline_var,
                        command=self.on_preference_change).pack(side="left", padx=(0, 15))

        self.filter_overdue_var = ctk.BooleanVar(value=self.manager.preferences.get("filter_overdue", False))
        ctk.CTkCheckBox(row2, text="Ukryj po terminie", variable=self.filter_overdue_var,
                        command=self.on_preference_change).pack(side="left")

        # 3. RAMKA KAFELKÓW (Wiersz 2) & 4. STRONICOWANIE (Wiersz 3)
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

        # KALENDARZ (Startowo schowany)
        self.calendar_view = CalendarView(self, self.manager, on_update_callback=self.refresh_all_views,
                                          edit_callback=self.edit_tile)

        self.draw_tiles()

    def switch_main_view(self, choice):
        if choice == "Tablica":
            self.cal_color_lbl.grid_remove()
            self.cal_color_switcher.grid_remove()
            self.col_lbl.grid()
            self.col_switcher.grid()

            if hasattr(self, "calendar_view"): self.calendar_view.grid_remove()
            self.filter_frame.grid()
            self.scrollable_frame.grid()
            self.pagination_frame.grid()
            self.draw_tiles(reset_page=False)
        else:
            self.col_lbl.grid_remove()
            self.col_switcher.grid_remove()
            self.cal_color_lbl.grid(row=0, column=4, sticky="e", padx=(0, 10))
            self.cal_color_switcher.grid(row=0, column=5, sticky="e", padx=(0, 20))

            self.filter_frame.grid_remove()
            self.scrollable_frame.grid_remove()
            self.pagination_frame.grid_remove()

            self.calendar_view.grid(row=1, column=0, rowspan=3, sticky="nsew", padx=20, pady=(10, 20))
            self.calendar_view.refresh_data()

    def refresh_all_views(self):
        self.draw_tiles(reset_page=False)

    def show_main_help(self):
        from ui_dialogs import HelpDialog
        ctx = "calendar" if self.main_view_var.get() == "Kalendarz" else "main"
        HelpDialog(self, context=ctx)
    def on_window_resize(self, event):
        if event.widget == self:
            current_width = self.winfo_width()
            if abs(current_width - self.last_width) > 50:
                self.last_width = current_width
                if self.resize_timer:
                    self.after_cancel(self.resize_timer)
                self.resize_timer = self.after(100, lambda: self.draw_tiles(reset_page=False))

    def schedule_search(self, *args):
        if self.search_timer: self.after_cancel(self.search_timer)
        self.search_timer = self.after(300, lambda: self.draw_tiles(reset_page=True))

    def save_current_preferences(self):
        self.manager.preferences["mode"] = self.mode_var.get()
        self.manager.preferences["columns"] = self.col_var.get()
        self.manager.preferences["theme"] = self.theme_var.get()
        self.manager.preferences["color_style"] = self.color_style_var.get()
        self.manager.preferences["sort_by"] = self.sort_var.get()
        self.manager.preferences["sort_order"] = self.sort_order_var.get()

        self.manager.preferences["filter_status"] = self.filter_status_var.get()
        self.manager.preferences["filter_wf"] = self.filter_wf_var.get()
        self.manager.preferences["filter_no_deadline"] = self.filter_no_deadline_var.get()
        self.manager.preferences["filter_overdue"] = self.filter_overdue_var.get()
        self.manager.save_to_file()

    def on_preference_change(self, *args):
        self.save_current_preferences()
        if self.main_view_var.get() == "Tablica":
            self.draw_tiles()
        else:
            if hasattr(self, "calendar_view"):
                self.calendar_view.refresh_data()

    def change_theme(self, theme_name, save=True):
        if theme_name == "Jasny":
            ctk.set_appearance_mode("Light")
        elif theme_name == "Ciemny":
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("System")
        if save: self.save_current_preferences()

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
        TileFormDialog(master=self, on_save_callback=self.save_new_tile)

    def save_new_tile(self, new_tile_model):
        self.manager.add_tile(new_tile_model)
        self.manager.save_to_file()
        self.draw_tiles(reset_page=True)
        if self.main_view_var.get() == "Kalendarz":
            self.calendar_view.refresh_data()

    def draw_tiles(self, reset_page=True):
        if reset_page: self.current_page = 1
        columns = int(self.col_var.get())
        is_compact = (self.mode_var.get() == "Skrócony")
        color_style = self.color_style_var.get()

        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        for i in range(10): self.scrollable_frame.grid_columnconfigure(i, weight=0)
        for i in range(columns): self.scrollable_frame.grid_columnconfigure(i, weight=1)

        query = self.search_var.get().lower().strip()
        filtered_tiles = [t for t in self.manager.tiles if
                          query in t.title.lower() or any(query in tag.lower() for tag in t.tags)]

        status_f = self.filter_status_var.get()
        if status_f == "Tylko Aktywne":
            filtered_tiles = [t for t in filtered_tiles if not t.is_completed]
        elif status_f == "Tylko Ukończone":
            filtered_tiles = [t for t in filtered_tiles if t.is_completed]

        wf_f = self.filter_wf_var.get()
        if wf_f == "Z Workflow":
            filtered_tiles = [t for t in filtered_tiles if t.has_workflow]
        elif wf_f == "Bez Workflow":
            filtered_tiles = [t for t in filtered_tiles if not t.has_workflow]

        if self.filter_no_deadline_var.get(): filtered_tiles = [t for t in filtered_tiles if t.deadline]
        if self.filter_overdue_var.get(): filtered_tiles = [t for t in filtered_tiles if
                                                            t.days_left is None or t.days_left >= 0]

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
        if self.current_page > total_pages: self.current_page = total_pages

        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        limited_tiles = filtered_tiles[start_idx:end_idx]

        self.page_label.configure(text=f"Strona {self.current_page} z {total_pages}")
        self.prev_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < total_pages else "disabled")

        app_width = self.winfo_width()
        if app_width < 250: app_width = st.WINDOW_WIDTH
        estimated_tile_width = (app_width - 80) / columns
        calculated_wrap = max(50, int(estimated_tile_width - 160))

        for index, tile_model in enumerate(limited_tiles):
            wiersz = index // columns
            kolumna = index % columns

            tile_widget = ProjectTileWidget(
                master=self.scrollable_frame,
                tile_model=tile_model,
                is_compact=is_compact,
                color_style=color_style,
                title_wrap=calculated_wrap,
                save_callback=self.manager.save_to_file,
                delete_callback=self.delete_tile,
                complete_callback=self.complete_tile,
                edit_callback=self.edit_tile,
                restore_callback=self.restore_tile,
                pin_callback=self.pin_tile,
                open_workflow_callback=self.open_workflow_view
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
        if self.main_view_var.get() == "Kalendarz": self.calendar_view.refresh_data()

    def delete_tile(self, tile_model):
        self.manager.tiles.remove(tile_model)
        self.manager.save_to_file()
        self.draw_tiles(reset_page=False)
        if self.main_view_var.get() == "Kalendarz": self.calendar_view.refresh_data()

    def complete_tile(self, tile_model):
        tile_model.is_completed = True
        tile_model.is_pinned = False
        self.manager.save_to_file()
        self.draw_tiles(reset_page=False)
        if self.main_view_var.get() == "Kalendarz": self.calendar_view.refresh_data()

    def edit_tile(self, tile_model):
        TileFormDialog(master=self, on_save_callback=self.update_existing_tile, existing_tile=tile_model)

    def update_existing_tile(self, updated_model):
        self.manager.save_to_file()
        self.draw_tiles(reset_page=False)
        if hasattr(self, "calendar_view") and self.main_view_var.get() == "Kalendarz":
            self.calendar_view.refresh_data()

    def open_workflow_view(self, tile_model):
        self.toolbar_frame.grid_remove()
        self.filter_frame.grid_remove()
        self.scrollable_frame.grid_remove()
        self.pagination_frame.grid_remove()
        if hasattr(self, "calendar_view"): self.calendar_view.grid_remove()

        self.workflow_view = WorkflowCanvasFrame(master=self, tile_model=tile_model,
                                                 close_callback=self.close_workflow_view, manager=self.manager)
        self.workflow_view.grid(row=0, column=0, rowspan=4, sticky="nsew")

    def close_workflow_view(self):
        self.workflow_view.destroy()
        self.toolbar_frame.grid()
        if self.main_view_var.get() == "Tablica":
            self.filter_frame.grid()
            self.scrollable_frame.grid()
            self.pagination_frame.grid()
            self.draw_tiles(reset_page=False)
        else:
            self.calendar_view.grid(row=1, column=0, rowspan=3, sticky="nsew", padx=20, pady=(10, 20))
            self.calendar_view.refresh_data()


if __name__ == "__main__":
    app = SmartProjectTilesApp()
    app.mainloop()