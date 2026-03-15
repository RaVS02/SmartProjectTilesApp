import customtkinter as ctk
import tkinter as tk
import calendar
from datetime import datetime
import settings as st
from translations import tr


class MiniTile(ctk.CTkFrame):
    def __init__(self, master, tile_model, drag_start_cb, drag_motion_cb, drag_release_cb, edit_cb, is_compact=True,
                 color_style="color_bg", **kwargs):
        self.tile_model = tile_model
        total_weight = self.tile_model.total_weight

        if self.tile_model.is_completed:
            bg_col, border_col = st.COMPLETED_TILE_COLOR, "gray"
        else:
            base_bg = self.tile_model.color if self.tile_model.color else st.DEFAULT_TILE_COLOR
            base_border = st.SUMMATIVE_COLORS.get(total_weight, st.DEFAULT_TILE_COLOR)

            # NAPRAWIONO: Literówka w nazwie zmiennej (border_col) i obsługa kluczy tłumaczeń
            if color_style in ["color_bg", "Kolorowe Tło"]:
                bg_col, border_col = base_bg, base_border
            elif color_style in ["color_border", "Tylko Ramki"]:
                bg_col, border_col = st.DEFAULT_TILE_COLOR, base_border
            else:
                bg_col, border_col = st.DEFAULT_TILE_COLOR, "gray"

        super().__init__(master, fg_color=bg_col, border_color=border_col, border_width=2, corner_radius=6, **kwargs)

        if is_compact:
            self.configure(height=30)
            self.pack_propagate(False)

        self.drag_start_cb, self.drag_motion_cb, self.drag_release_cb = drag_start_cb, drag_motion_cb, drag_release_cb
        self.edit_cb = edit_cb

        title_text = tile_model.title
        if tile_model.is_completed: title_text = "✅ " + title_text

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=(2, 0) if not is_compact else 2)

        self.lbl = ctk.CTkLabel(header_frame, text=title_text, font=("Helvetica", 11, "bold"),
                                text_color=("black", "#DCE4EE"), anchor="w", wraplength=120 if not is_compact else 0)
        self.lbl.pack(side="left", fill="x", expand=True)

        if not is_compact:
            dot_color = st.PRIORITY_COLORS.get(self.tile_model.priority, "gray")
            ctk.CTkFrame(header_frame, width=8, height=8, corner_radius=4, fg_color=dot_color).pack(side="right",
                                                                                                    padx=(5, 0), pady=4)
            if self.tile_model.tags:
                tags_str = " ".join([f"#{t}" for t in self.tile_model.tags])
                ctk.CTkLabel(self, text=tags_str, font=("Helvetica", 9, "italic"), text_color="gray", anchor="w").pack(
                    fill="x", padx=5, pady=(0, 4))

        bind_widgets = [self, header_frame, self.lbl]
        for widget in bind_widgets:
            widget.bind("<ButtonPress-1>", self.on_press)
            widget.bind("<B1-Motion>", self.on_motion)
            widget.bind("<ButtonRelease-1>", self.on_release)
            widget.bind("<Double-Button-1>", self.on_double_click)

    def on_double_click(self, event):
        self.edit_cb(self.tile_model)

    def on_press(self, event):
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._is_dragging = False

    def on_motion(self, event):
        if not getattr(self, "_is_dragging", False):
            if abs(event.x_root - getattr(self, "_drag_start_x", event.x_root)) > 5 or abs(
                    event.y_root - getattr(self, "_drag_start_y", event.y_root)) > 5:
                self._is_dragging = True
                self.drag_start_cb(self, event)
        if getattr(self, "_is_dragging", False):
            self.drag_motion_cb(self, event)

    def on_release(self, event):
        if getattr(self, "_is_dragging", False): self.drag_release_cb(self, event)
        self._is_dragging = False


class CalendarView(ctk.CTkFrame):
    def __init__(self, master, manager, on_update_callback, edit_callback, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.manager = manager
        self.on_update_callback = on_update_callback
        self.edit_callback = edit_callback

        today = datetime.now()
        self.current_year = today.year
        self.current_month = today.month

        self.drop_zones = {}
        self._pending_drop_zones = {}
        self._drop_zone_timer = None
        self.drag_ghost = None
        self.dragged_tile_model = None
        self.build_ui()

    def build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.backlog_frame = ctk.CTkFrame(self, width=250, corner_radius=10)
        self.backlog_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.backlog_frame.grid_propagate(False)

        ctk.CTkLabel(self.backlog_frame, text=tr("cal_backlog"), font=st.FONT_TITLE).pack(pady=15)
        ctk.CTkLabel(self.backlog_frame, text=tr("cal_backlog_desc"), font=("Helvetica", 10, "italic"),
                     text_color="gray").pack(pady=(0, 10))

        self.backlog_scroll = ctk.CTkScrollableFrame(self.backlog_frame, fg_color="transparent")
        self.backlog_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        self.cal_container = ctk.CTkFrame(self, fg_color="transparent")
        self.cal_container.grid(row=0, column=1, sticky="nsew")
        self.cal_container.grid_rowconfigure(1, weight=1)
        self.cal_container.grid_columnconfigure(0, weight=1)

        nav_frame = ctk.CTkFrame(self.cal_container, height=50, corner_radius=10)
        nav_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkButton(nav_frame, text=tr("cal_prev"), width=100, command=self.prev_month).pack(side="left", padx=10,
                                                                                               pady=10)
        self.month_year_lbl = ctk.CTkLabel(nav_frame, text="", font=st.FONT_TITLE)
        self.month_year_lbl.pack(side="left", expand=True)
        ctk.CTkButton(nav_frame, text=tr("cal_today"), width=80, fg_color="#1f538d", command=self.go_today).pack(
            side="right", padx=(0, 10), pady=10)
        ctk.CTkButton(nav_frame, text=tr("cal_next"), width=100, command=self.next_month).pack(side="right", padx=10,
                                                                                               pady=10)

        self.grid_frame = ctk.CTkFrame(self.cal_container, corner_radius=10)
        self.grid_frame.grid(row=1, column=0, sticky="nsew")
        for i in range(7): self.grid_frame.grid_columnconfigure(i, weight=1, uniform="col")

        for i, dzien in enumerate(tr("cal_weekdays")):
            ctk.CTkLabel(self.grid_frame, text=dzien, font=("Helvetica", 12, "bold"), text_color="gray").grid(row=0,
                                                                                                              column=i,
                                                                                                              pady=5)

        self.refresh_data()

    def prev_month(self):
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.refresh_data()

    def next_month(self):
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self.refresh_data()

    def go_today(self):
        today = datetime.now()
        self.current_year = today.year
        self.current_month = today.month
        self.refresh_data()

    def refresh_data(self):
        for widget in self.grid_frame.winfo_children():
            if int(widget.grid_info()["row"]) > 0: widget.destroy()
        for widget in self.backlog_scroll.winfo_children(): widget.destroy()

        self.drop_zones.clear()
        self._pending_drop_zones.clear()

        mies_str = tr("cal_months")[self.current_month]
        self.month_year_lbl.configure(text=f"{mies_str} {self.current_year}")

        unscheduled_tiles = []
        scheduled_tiles = {}
        for t in self.manager.tiles:
            if getattr(t, "is_archived", False): continue
            if not t.deadline:
                unscheduled_tiles.append(t)
            else:
                if t.deadline not in scheduled_tiles: scheduled_tiles[t.deadline] = []
                scheduled_tiles[t.deadline].append(t)

        is_compact = (self.manager.preferences.get("mode", "size_full") == "size_compact")
        color_style = self.manager.preferences.get("color_style", "color_bg")

        for t in unscheduled_tiles:
            mt = MiniTile(self.backlog_scroll, t, self.on_drag_start, self.on_drag_motion, self.on_drag_release,
                          self.edit_callback, is_compact=is_compact, color_style=color_style)
            mt.pack(fill="x", pady=2)

        self._pending_drop_zones["UNSCHEDULED"] = self.backlog_frame
        cal = calendar.monthcalendar(self.current_year, self.current_month)
        today_date = datetime.now().strftime("%Y-%m-%d")

        for r_idx, week in enumerate(cal):
            self.grid_frame.grid_rowconfigure(r_idx + 1, weight=1, uniform="row")
            for c_idx, day in enumerate(week):
                cell_frame = ctk.CTkFrame(self.grid_frame, fg_color=("gray85", "gray15"), corner_radius=5)
                cell_frame.grid(row=r_idx + 1, column=c_idx, sticky="nsew", padx=2, pady=2)

                if day != 0:
                    date_str = f"{self.current_year}-{self.current_month:02d}-{day:02d}"
                    is_today = (date_str == today_date)

                    header_col = "#ff4a4a" if is_today else ("black", "white")
                    day_lbl = ctk.CTkLabel(cell_frame, text=str(day), font=("Helvetica", 14, "bold"),
                                           text_color=header_col)
                    day_lbl.pack(anchor="ne", padx=5, pady=2)

                    day_content = ctk.CTkScrollableFrame(cell_frame, fg_color="transparent")
                    day_content.pack(fill="both", expand=True)

                    if date_str in scheduled_tiles:
                        for t in scheduled_tiles[date_str]:
                            mt = MiniTile(day_content, t, self.on_drag_start, self.on_drag_motion, self.on_drag_release,
                                          self.edit_callback, is_compact=is_compact, color_style=color_style)
                            mt.pack(fill="x", pady=2)

                    self._pending_drop_zones[date_str] = cell_frame
                else:
                    cell_frame.configure(fg_color=("gray90", "gray10"))

        if self._drop_zone_timer: self.after_cancel(self._drop_zone_timer)
        self._drop_zone_timer = self.after(100, self._calculate_all_drop_zones)

    def _calculate_all_drop_zones(self):
        self.update_idletasks()
        self.drop_zones.clear()
        for name, widget in self._pending_drop_zones.items():
            if widget.winfo_exists():
                x1 = widget.winfo_rootx()
                y1 = widget.winfo_rooty()
                x2 = x1 + widget.winfo_width()
                y2 = y1 + widget.winfo_height()
                self.drop_zones[name] = (x1, y1, x2, y2)

    def on_drag_start(self, minitile, event):
        self.dragged_tile_model = minitile.tile_model
        self.drag_ghost = tk.Toplevel(self)
        self.drag_ghost.overrideredirect(True)
        self.drag_ghost.attributes('-alpha', 0.8)
        self.drag_ghost.attributes('-topmost', True)

        bg_col = self.dragged_tile_model.color[1] if isinstance(self.dragged_tile_model.color, tuple) else (
                    self.dragged_tile_model.color or "#1e1e1e")
        if self.dragged_tile_model.is_completed: bg_col = "#1a1a1a"

        ghost_frame = tk.Frame(self.drag_ghost, bg=bg_col, bd=2, relief="ridge")
        ghost_frame.pack(fill="both", expand=True)
        tk.Label(ghost_frame, text=self.dragged_tile_model.title, fg="white", bg=bg_col, font=("Helvetica", 10)).pack(
            padx=10, pady=5)
        self.drag_ghost.geometry(f"150x30+{event.x_root + 10}+{event.y_root + 10}")

    def on_drag_motion(self, minitile, event):
        if self.drag_ghost: self.drag_ghost.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

    def on_drag_release(self, minitile, event):
        if self.drag_ghost:
            self.drag_ghost.destroy()
            self.drag_ghost = None

        rx, ry = event.x_root, event.y_root
        target_zone = None

        for name, (x1, y1, x2, y2) in self.drop_zones.items():
            if x1 <= rx <= x2 and y1 <= ry <= y2:
                target_zone = name
                break

        if target_zone:
            if target_zone == "UNSCHEDULED":
                self.dragged_tile_model.deadline = None
            else:
                self.dragged_tile_model.deadline = target_zone
            self.manager.save_to_file()
            self.on_update_callback()
            self.refresh_data()
        self.dragged_tile_model = None