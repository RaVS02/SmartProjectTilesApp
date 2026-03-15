import customtkinter as ctk
import settings as st
import math
import tkinter.messagebox as messagebox
from models import TileManager
from ui import ProjectTileWidget
from ui_dialogs import TileFormDialog
from ui_workflow import WorkflowCanvasFrame
from ui_calendar import CalendarView
from ui_statistics import StatisticsView

from translations import set_lang, tr, LANGUAGES

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("green")


class SmartProjectTilesApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(st.WINDOW_TITLE)
        self.geometry(f"{st.WINDOW_WIDTH}x{st.WINDOW_HEIGHT}")
        try:
            self.iconbitmap("appico.ico")
        except Exception:
            pass  # Jeśli program nie znajdzie pliku, po prostu to zignoruje i nie wywali błędu
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
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        # --- ZMIANA: Inicjalizacja globalnego języka ---
        self.lang = self.manager.preferences.get("language", "pl")
        set_lang(self.lang)

        self.view_keys = ["view_board", "view_calendar", "view_stats"]
        self.size_keys = ["size_full", "size_compact"]
        self.color_keys = ["color_bg", "color_border", "color_minimal"]
        self.theme_keys = ["theme_light", "theme_dark", "theme_system"]
        self.sort_keys = ["sort_weight", "sort_deadline", "sort_priority", "sort_name", "sort_tags"]
        self.order_keys = ["sort_asc", "sort_desc"]
        self.status_keys = ["filter_all", "filter_active", "filter_done"]
        self.wf_keys = ["filter_all", "filter_with_wf", "filter_no_wf"]
        self.tasks_keys = ["filter_all", "filter_with_tasks", "filter_no_tasks"]

        def _mig(pref_key, keys_list):
            val = self.manager.preferences.get(pref_key, keys_list[0])
            return val if val in keys_list else keys_list[0]

        v_main_view = _mig("main_view", self.view_keys)
        v_mode = _mig("mode", self.size_keys)
        v_color = _mig("color_style", self.color_keys)
        v_theme = _mig("theme", self.theme_keys)
        v_sort = _mig("sort_by", self.sort_keys)
        v_order = _mig("sort_order", self.order_keys)
        v_status = _mig("filter_status", self.status_keys)
        v_wf = _mig("filter_wf", self.wf_keys)
        v_tasks = _mig("filter_tasks", self.tasks_keys)

        self.change_theme(v_theme, save=False)

        self.toolbar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        self.toolbar_frame.grid_columnconfigure(2, weight=1)

        self.add_btn = ctk.CTkButton(self.toolbar_frame, text=tr("add_btn"), font=st.FONT_TITLE,
                                     command=self.open_add_dialog)
        self.add_btn.grid(row=0, column=0, sticky="w")

        self.main_view_var = ctk.StringVar(value=tr(v_main_view))
        self.main_view_switcher = ctk.CTkSegmentedButton(self.toolbar_frame, values=[tr(k) for k in self.view_keys],
                                                         variable=self.main_view_var, command=self.switch_main_view,
                                                         font=("Helvetica", 14, "bold"))
        self.main_view_switcher.grid(row=0, column=1, sticky="w", padx=(20, 0))

        ctk.CTkLabel(self.toolbar_frame, text=tr("size")).grid(row=0, column=2, sticky="e", padx=(0, 10))
        self.mode_var = ctk.StringVar(value=tr(v_mode))
        self.mode_switcher = ctk.CTkSegmentedButton(self.toolbar_frame, values=[tr(k) for k in self.size_keys],
                                                    variable=self.mode_var, command=self.on_preference_change)
        self.mode_switcher.grid(row=0, column=3, sticky="e", padx=(0, 20))

        self.col_lbl = ctk.CTkLabel(self.toolbar_frame, text=tr("columns"))
        self.col_lbl.grid(row=0, column=4, sticky="e", padx=(0, 10))
        self.col_var = ctk.StringVar(value=self.manager.preferences.get("columns", "3"))
        self.col_switcher = ctk.CTkSegmentedButton(self.toolbar_frame, values=["1", "2", "3", "4", "5"],
                                                   variable=self.col_var, command=self.on_preference_change)
        self.col_switcher.grid(row=0, column=5, sticky="e", padx=(0, 20))

        self.color_style_var = ctk.StringVar(value=tr(v_color))
        self.cal_color_lbl = ctk.CTkLabel(self.toolbar_frame, text=tr("colors"))
        self.cal_color_switcher = ctk.CTkOptionMenu(self.toolbar_frame, values=[tr(k) for k in self.color_keys],
                                                    variable=self.color_style_var, command=self.on_preference_change,
                                                    width=130)

        ctk.CTkLabel(self.toolbar_frame, text=tr("theme")).grid(row=0, column=6, sticky="e", padx=(0, 10))
        self.theme_var = ctk.StringVar(value=tr(v_theme))
        self.theme_switcher = ctk.CTkSegmentedButton(self.toolbar_frame, values=[tr(k) for k in self.theme_keys],
                                                     variable=self.theme_var,
                                                     command=lambda v: self.change_theme(self._rv(v, self.theme_keys)))
        self.theme_switcher.grid(row=0, column=7, sticky="e", padx=(0, 20))

        current_lang_name = "English" if self.lang == "en" else "Polski"
        self.lang_var = ctk.StringVar(value=current_lang_name)
        self.lang_switcher = ctk.CTkOptionMenu(self.toolbar_frame, values=list(LANGUAGES.keys()),
                                               variable=self.lang_var, command=self.change_language, width=90)
        self.lang_switcher.grid(row=0, column=8, sticky="e", padx=(0, 10))

        self.help_btn = ctk.CTkButton(self.toolbar_frame, text="❓", width=30, command=self.show_main_help,
                                      fg_color="#1f538d")
        self.help_btn.grid(row=0, column=9, sticky="e", padx=(10, 0))

        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 0))

        row1 = ctk.CTkFrame(self.filter_frame, fg_color="transparent")
        row1.pack(fill="x", pady=2)
        row1.grid_columnconfigure(0, weight=1)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.schedule_search)
        self.search_entry = ctk.CTkEntry(row1, textvariable=self.search_var, placeholder_text=tr("search_placeholder"),
                                         width=250)
        self.search_entry.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(row1, text=tr("colors")).grid(row=0, column=1, sticky="e", padx=(0, 10))
        ctk.CTkOptionMenu(row1, values=[tr(k) for k in self.color_keys], variable=self.color_style_var,
                          command=self.on_preference_change, width=130).grid(row=0, column=2, sticky="e", padx=(0, 20))

        ctk.CTkLabel(row1, text=tr("sort_by")).grid(row=0, column=3, sticky="e", padx=(0, 10))
        self.sort_var = ctk.StringVar(value=tr(v_sort))
        ctk.CTkOptionMenu(row1, values=[tr(k) for k in self.sort_keys], variable=self.sort_var,
                          command=self.on_preference_change, width=160).grid(row=0, column=4, sticky="e")

        self.sort_order_var = ctk.StringVar(value=tr(v_order))
        ctk.CTkButton(row1, textvariable=self.sort_order_var, width=100, command=self.toggle_sort_order).grid(row=0,
                                                                                                              column=5,
                                                                                                              sticky="e",
                                                                                                              padx=(10,
                                                                                                                    0))

        row2 = ctk.CTkFrame(self.filter_frame, fg_color="transparent")
        row2.pack(fill="x", pady=5)

        ctk.CTkLabel(row2, text=tr("status")).pack(side="left", padx=(0, 5))
        self.filter_status_var = ctk.StringVar(value=tr(v_status))
        ctk.CTkOptionMenu(row2, values=[tr(k) for k in self.status_keys], variable=self.filter_status_var,
                          command=self.on_preference_change, width=130).pack(side="left", padx=(0, 15))

        ctk.CTkLabel(row2, text=tr("workflow")).pack(side="left", padx=(0, 5))
        self.filter_wf_var = ctk.StringVar(value=tr(v_wf))
        ctk.CTkOptionMenu(row2, values=[tr(k) for k in self.wf_keys], variable=self.filter_wf_var,
                          command=self.on_preference_change, width=130).pack(side="left", padx=(0, 15))

        ctk.CTkLabel(row2, text=tr("tasks")).pack(side="left", padx=(0, 5))
        self.filter_tasks_var = ctk.StringVar(value=tr(v_tasks))
        ctk.CTkOptionMenu(row2, values=[tr(k) for k in self.tasks_keys], variable=self.filter_tasks_var,
                          command=self.on_preference_change, width=130).pack(side="left", padx=(0, 15))

        self.filter_no_deadline_var = ctk.BooleanVar(value=self.manager.preferences.get("filter_no_deadline", False))
        ctk.CTkCheckBox(row2, text=tr("hide_no_deadline"), variable=self.filter_no_deadline_var,
                        command=self.on_preference_change).pack(side="left", padx=(0, 10))

        self.filter_overdue_var = ctk.BooleanVar(value=self.manager.preferences.get("filter_overdue", False))
        ctk.CTkCheckBox(row2, text=tr("hide_overdue"), variable=self.filter_overdue_var,
                        command=self.on_preference_change).pack(side="left")

        self.filter_archive_var = ctk.BooleanVar(value=False)
        self.archive_cb = ctk.CTkCheckBox(row2, text=tr("show_trash"), variable=self.filter_archive_var,
                                          command=self.on_preference_change, fg_color="#8b0000")
        self.archive_cb.pack(side="right", padx=(10, 0))

        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 10))

        self.pagination_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.pagination_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 15))
        self.pagination_frame.grid_columnconfigure(1, weight=1)

        self.prev_btn = ctk.CTkButton(self.pagination_frame, text=tr("page_prev"), width=100, command=self.prev_page)
        self.prev_btn.grid(row=0, column=0, sticky="w")
        self.page_label = ctk.CTkLabel(self.pagination_frame, text="", font=st.FONT_DEFAULT)
        self.page_label.grid(row=0, column=1, sticky="ew")
        self.next_btn = ctk.CTkButton(self.pagination_frame, text=tr("page_next"), width=100, command=self.next_page)
        self.next_btn.grid(row=0, column=2, sticky="e")

        self.calendar_view = CalendarView(self, self.manager, on_update_callback=self.refresh_all_views,
                                          edit_callback=self.edit_tile)
        self.stats_view = StatisticsView(self, self.manager)

        # ZMIANA: Zamiast rysować w ciemno tablicę, każemy programowi "kliknąć" w zapamiętaną zakładkę
        self.switch_main_view(self.main_view_var.get())

        self.draw_tiles()

    def _rv(self, display_string, key_list):
        for k in key_list:
            if tr(k) == display_string: return k
        return key_list[0]

    def change_language(self, choice):
        new_lang_code = LANGUAGES[choice]
        if new_lang_code != self.lang:
            self.manager.preferences["language"] = new_lang_code
            self.save_current_preferences()
            for widget in self.winfo_children(): widget.destroy()
            self.setup_ui()

    def show_main_help(self):
        from ui_dialogs import HelpDialog
        view = self._rv(self.main_view_var.get(), self.view_keys)
        if view == "view_calendar":
            ctx = "calendar"
        elif view == "view_stats":
            ctx = "statistics"
        else:
            ctx = "main"
        HelpDialog(self, context=ctx)

    def switch_main_view(self, choice):
        view_key = self._rv(choice, self.view_keys)

        if hasattr(self, "calendar_view"): self.calendar_view.grid_remove()
        if hasattr(self, "stats_view"): self.stats_view.grid_remove()
        self.filter_frame.grid_remove()
        self.scrollable_frame.grid_remove()
        self.pagination_frame.grid_remove()
        self.cal_color_lbl.grid_remove()
        self.cal_color_switcher.grid_remove()
        self.col_lbl.grid_remove()
        self.col_switcher.grid_remove()
        self.mode_switcher.configure(state="disabled")

        if view_key == "view_board":
            self.mode_switcher.configure(state="normal")
            self.col_lbl.grid(row=0, column=4, sticky="e", padx=(0, 10))
            self.col_switcher.grid(row=0, column=5, sticky="e", padx=(0, 20))
            self.filter_frame.grid()
            self.scrollable_frame.grid()
            self.pagination_frame.grid()
            self.draw_tiles(reset_page=False)
        elif view_key == "view_calendar":
            self.mode_switcher.configure(state="normal")
            self.cal_color_lbl.grid(row=0, column=4, sticky="e", padx=(0, 10))
            self.cal_color_switcher.grid(row=0, column=5, sticky="e", padx=(0, 20))
            self.calendar_view.grid(row=1, column=0, rowspan=3, sticky="nsew", padx=20, pady=(10, 20))
            self.calendar_view.refresh_data()
        elif view_key == "view_stats":
            self.stats_view.grid(row=1, column=0, rowspan=3, sticky="nsew", padx=20, pady=20)
            self.stats_view.refresh_data()

    def refresh_all_views(self):
        self.draw_tiles(reset_page=False)
        if hasattr(self, "stats_view"): self.stats_view.refresh_data()

    def on_window_resize(self, event):
        if event.widget == self:
            current_width = self.winfo_width()
            if abs(current_width - self.last_width) > 50:
                self.last_width = current_width
                if self.resize_timer: self.after_cancel(self.resize_timer)
                self.resize_timer = self.after(100, lambda: self.draw_tiles(reset_page=False))

    def schedule_search(self, *args):
        if self.search_timer: self.after_cancel(self.search_timer)
        self.search_timer = self.after(300, lambda: self.draw_tiles(reset_page=True))

    def save_current_preferences(self):
        self.manager.preferences["main_view"] = self._rv(self.main_view_var.get(), self.view_keys)
        self.manager.preferences["mode"] = self._rv(self.mode_var.get(), self.size_keys)
        self.manager.preferences["color_style"] = self._rv(self.color_style_var.get(), self.color_keys)
        self.manager.preferences["theme"] = self._rv(self.theme_var.get(), self.theme_keys)
        self.manager.preferences["sort_by"] = self._rv(self.sort_var.get(), self.sort_keys)
        self.manager.preferences["sort_order"] = self._rv(self.sort_order_var.get(), self.order_keys)
        self.manager.preferences["filter_status"] = self._rv(self.filter_status_var.get(), self.status_keys)
        self.manager.preferences["filter_wf"] = self._rv(self.filter_wf_var.get(), self.wf_keys)
        self.manager.preferences["filter_tasks"] = self._rv(self.filter_tasks_var.get(), self.tasks_keys)

        self.manager.preferences["columns"] = self.col_var.get()
        self.manager.preferences["filter_no_deadline"] = self.filter_no_deadline_var.get()
        self.manager.preferences["filter_overdue"] = self.filter_overdue_var.get()
        self.manager.save_to_file()

    def on_preference_change(self, *args):
        self.save_current_preferences()
        view = self._rv(self.main_view_var.get(), self.view_keys)
        if view == "view_board":
            self.draw_tiles()
        elif view == "view_calendar":
            if hasattr(self, "calendar_view"): self.calendar_view.refresh_data()

    def change_theme(self, theme_key, save=True):
        if theme_key == "theme_light":
            ctk.set_appearance_mode("Light")
        elif theme_key == "theme_dark":
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
        current = self._rv(self.sort_order_var.get(), self.order_keys)
        self.sort_order_var.set(tr("sort_desc") if current == "sort_asc" else tr("sort_asc"))
        self.on_preference_change()

    def open_add_dialog(self):
        TileFormDialog(master=self, on_save_callback=self.save_new_tile)

    def save_new_tile(self, new_tile_model):
        self.manager.add_tile(new_tile_model)
        self.manager.save_to_file()
        self.refresh_all_views()
        if self._rv(self.main_view_var.get(), self.view_keys) == "view_calendar": self.calendar_view.refresh_data()

    def draw_tiles(self, reset_page=True):
        if reset_page: self.current_page = 1
        columns = int(self.col_var.get())

        mode_key = self._rv(self.mode_var.get(), self.size_keys)
        is_compact = (mode_key == "size_compact")

        color_style = "Kolorowe Tło"
        cs_key = self._rv(self.color_style_var.get(), self.color_keys)
        if cs_key == "color_border":
            color_style = "Tylko Ramki"
        elif cs_key == "color_minimal":
            color_style = "Minimalistyczny"

        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        for i in range(10): self.scrollable_frame.grid_columnconfigure(i, weight=0)
        for i in range(columns): self.scrollable_frame.grid_columnconfigure(i, weight=1)

        show_archive = self.filter_archive_var.get()
        if show_archive:
            filtered_tiles = [t for t in self.manager.tiles if getattr(t, "is_archived", False)]
        else:
            filtered_tiles = [t for t in self.manager.tiles if not getattr(t, "is_archived", False)]

        query = self.search_var.get().lower().strip()
        filtered_tiles = [t for t in filtered_tiles if
                          query in t.title.lower() or any(query in tag.lower() for tag in t.tags)]

        st_key = self._rv(self.filter_status_var.get(), self.status_keys)
        if st_key == "filter_active":
            filtered_tiles = [t for t in filtered_tiles if not t.is_completed]
        elif st_key == "filter_done":
            filtered_tiles = [t for t in filtered_tiles if t.is_completed]

        wf_key = self._rv(self.filter_wf_var.get(), self.wf_keys)
        if wf_key == "filter_with_wf":
            filtered_tiles = [t for t in filtered_tiles if t.has_workflow]
        elif wf_key == "filter_no_wf":
            filtered_tiles = [t for t in filtered_tiles if not t.has_workflow]

        ts_key = self._rv(self.filter_tasks_var.get(), self.tasks_keys)
        if ts_key == "filter_with_tasks":
            filtered_tiles = [t for t in filtered_tiles if len(t.content.get("todos", [])) > 0]
        elif ts_key == "filter_no_tasks":
            filtered_tiles = [t for t in filtered_tiles if len(t.content.get("todos", [])) == 0]

        if self.filter_no_deadline_var.get(): filtered_tiles = [t for t in filtered_tiles if t.deadline]
        if self.filter_overdue_var.get(): filtered_tiles = [t for t in filtered_tiles if
                                                            t.days_left is None or t.days_left >= 0]

        sort_mode = self._rv(self.sort_var.get(), self.sort_keys)
        is_descending = self._rv(self.sort_order_var.get(), self.order_keys) == "sort_desc"

        if sort_mode == "sort_weight":
            filtered_tiles.sort(key=lambda x: x.total_weight, reverse=is_descending)
        elif sort_mode == "sort_deadline":
            filtered_tiles.sort(
                key=lambda x: x.days_left if x.days_left is not None else (9999 if not is_descending else -9999),
                reverse=is_descending)
        elif sort_mode == "sort_priority":
            filtered_tiles.sort(key=lambda x: st.PRIORITY_RANK.get(x.priority, 5), reverse=is_descending)
        elif sort_mode == "sort_name":
            filtered_tiles.sort(key=lambda x: x.title.lower(), reverse=is_descending)
        elif sort_mode == "sort_tags":
            filtered_tiles.sort(key=lambda x: x.tags[0].lower() if x.tags else "zzz", reverse=is_descending)

        filtered_tiles.sort(key=lambda x: x.is_pinned, reverse=True)
        filtered_tiles.sort(key=lambda x: x.is_completed, reverse=False)

        total_pages = max(1, math.ceil(len(filtered_tiles) / self.items_per_page))
        if self.current_page > total_pages: self.current_page = total_pages

        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        limited_tiles = filtered_tiles[start_idx:end_idx]

        self.page_label.configure(text=tr("page_info", self.current_page, total_pages))
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
                save_callback=self.save_and_refresh,
                archive_callback=self.archive_tile,
                recover_callback=self.recover_tile,
                permadelete_callback=self.permadelete_tile,
                complete_callback=self.complete_tile,
                edit_callback=self.edit_tile,
                restore_callback=self.restore_tile,
                pin_callback=self.pin_tile,
                open_workflow_callback=self.open_workflow_view
            )
            tile_widget.grid(row=wiersz, column=kolumna, padx=10, pady=10, sticky="nsew")

    def save_and_refresh(self):
        self.manager.save_to_file()
        if hasattr(self, "stats_view"): self.stats_view.refresh_data()

    def archive_tile(self, tile_model):
        tile_model.is_archived = True
        tile_model.is_pinned = False
        self.manager.save_to_file()
        self.refresh_all_views()
        if self._rv(self.main_view_var.get(), self.view_keys) == "view_calendar": self.calendar_view.refresh_data()

    def recover_tile(self, tile_model):
        tile_model.is_archived = False
        self.manager.save_to_file()
        self.refresh_all_views()
        if self._rv(self.main_view_var.get(), self.view_keys) == "view_calendar": self.calendar_view.refresh_data()

    def permadelete_tile(self, tile_model):
        if messagebox.askyesno(tr("confirm_title"), tr("confirm_delete", tile_model.title)):
            self.manager.tiles.remove(tile_model)
            self.manager.save_to_file()
            self.refresh_all_views()
            if self._rv(self.main_view_var.get(), self.view_keys) == "view_calendar": self.calendar_view.refresh_data()

    def pin_tile(self, tile_model):
        tile_model.is_pinned = not tile_model.is_pinned
        self.manager.save_to_file()
        self.draw_tiles(reset_page=False)

    def restore_tile(self, tile_model):
        tile_model.is_completed = False
        self.manager.save_to_file()
        self.refresh_all_views()
        if self._rv(self.main_view_var.get(), self.view_keys) == "view_calendar": self.calendar_view.refresh_data()

    def complete_tile(self, tile_model):
        tile_model.is_completed = True
        tile_model.is_pinned = False
        self.manager.save_to_file()
        self.refresh_all_views()
        if self._rv(self.main_view_var.get(), self.view_keys) == "view_calendar": self.calendar_view.refresh_data()

    def edit_tile(self, tile_model):
        TileFormDialog(master=self, on_save_callback=self.update_existing_tile, existing_tile=tile_model)

    def update_existing_tile(self, updated_model):
        self.manager.save_to_file()
        self.refresh_all_views()
        if hasattr(self, "calendar_view") and self._rv(self.main_view_var.get(), self.view_keys) == "view_calendar":
            self.calendar_view.refresh_data()

    def open_workflow_view(self, tile_model):
        self.toolbar_frame.grid_remove()
        self.filter_frame.grid_remove()
        self.scrollable_frame.grid_remove()
        self.pagination_frame.grid_remove()
        if hasattr(self, "calendar_view"): self.calendar_view.grid_remove()
        if hasattr(self, "stats_view"): self.stats_view.grid_remove()

        self.workflow_view = WorkflowCanvasFrame(master=self, tile_model=tile_model,
                                                 close_callback=self.close_workflow_view, manager=self.manager)
        self.workflow_view.grid(row=0, column=0, rowspan=4, sticky="nsew")

    def close_workflow_view(self):
        self.workflow_view.destroy()
        self.toolbar_frame.grid()

        view = self._rv(self.main_view_var.get(), self.view_keys)
        if view == "view_board":
            self.filter_frame.grid()
            self.scrollable_frame.grid()
            self.pagination_frame.grid()
            self.draw_tiles(reset_page=False)
        elif view == "view_calendar":
            self.calendar_view.grid(row=1, column=0, rowspan=3, sticky="nsew", padx=20, pady=(10, 20))
            self.calendar_view.refresh_data()
        elif view == "view_stats":
            self.stats_view.grid(row=1, column=0, rowspan=3, sticky="nsew", padx=20, pady=20)
            self.stats_view.refresh_data()

    def on_closing(self):
        if hasattr(self, "workflow_view") and self.workflow_view.winfo_exists():
            if getattr(self.workflow_view, "has_unsaved_changes", False):
                if not messagebox.askyesno(tr("unsaved_title"), tr("unsaved_desc")):
                    return
        try:
            self.save_current_preferences()
            self.manager.save_to_file()
        except Exception as e:
            print(f"Błąd przy końcowym zapisie: {e}")

        self.destroy()


if __name__ == "__main__":
    app = SmartProjectTilesApp()
    app.mainloop()