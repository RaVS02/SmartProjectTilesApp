import customtkinter as ctk
import settings as st
from models import ProjectTileModel
from tkcalendar import DateEntry  # <--- NOWY IMPORT
from datetime import datetime


class ProjectTileWidget(ctk.CTkFrame):
    # ZMIANA: Dodajemy argument title_wrap (domyślnie 200)
    def __init__(self, master, tile_model, is_compact=False, color_style="Kolorowe Tło",
                 save_callback=None, delete_callback=None, complete_callback=None,
                 edit_callback=None, restore_callback=None, pin_callback=None,
                 open_workflow_callback=None,  # <--- NOWY CALLBACK
                 title_wrap=200, **kwargs):
        self.model = tile_model
        self.is_compact = is_compact
        self.color_style = color_style
        self.title_wrap = title_wrap  # <--- Zapisujemy wyliczoną szerokość

        self.save_callback, self.delete_callback, self.complete_callback = save_callback, delete_callback, complete_callback
        self.edit_callback, self.restore_callback, self.pin_callback = edit_callback, restore_callback, pin_callback
        self.open_workflow_callback = open_workflow_callback
        # --- LOGIKA PERSONALIZACJI KOLORÓW ---
        total_weight = self.model.total_weight
        if self.model.is_completed:
            bg_color, border_color = st.COMPLETED_TILE_COLOR, "gray"
        else:
            base_bg = self.model.color if self.model.color else st.DEFAULT_TILE_COLOR
            base_border = st.SUMMATIVE_COLORS.get(total_weight, st.DEFAULT_TILE_COLOR)

            if self.color_style == "Kolorowe Tło":
                bg_color, border_color = base_bg, base_border
            elif self.color_style == "Tylko Ramki":
                bg_color, border_color = st.DEFAULT_TILE_COLOR, base_border
            else:  # "Minimalistyczny"
                bg_color, border_color = st.DEFAULT_TILE_COLOR, "gray"

        super().__init__(master, fg_color=bg_color, border_color=border_color, border_width=2, corner_radius=10,
                         **kwargs)
        self.build_ui()

    def build_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ==========================================
        # SEKCJA 1: NAGŁÓWEK
        # ==========================================
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        # ZMIANA: Używamy sztywnego 'wraplength' wstrzykniętego przez główne okno!
        # Usunęliśmy stąd header.bind("<Configure>", ...)
        title_label = ctk.CTkLabel(header, text=self.model.title, font=st.FONT_TITLE, justify="left",
                                   wraplength=self.title_wrap)
        title_label.grid(row=0, column=0, sticky="w")



        p_frame = ctk.CTkFrame(header, fg_color="transparent")
        p_frame.grid(row=0, column=1, sticky="e")

        dot_color = st.PRIORITY_COLORS.get(self.model.priority, "gray")
        ctk.CTkFrame(p_frame, width=10, height=10, corner_radius=5, fg_color=dot_color).pack(side="left", padx=5)

        # ZMIANA 1: Zwiększona widoczność tekstu priorytetu (większa czcionka, gruba, wyższy kontrast)
        priority_text = st.PRIORITY_LABELS.get(self.model.priority, "")
        ctk.CTkLabel(p_frame, text=priority_text, font=("Helvetica", 11, "bold"),
                     text_color=("#444444", "#cccccc")).pack(side="left")

        # ZMIANA 2: Pinezka z dopasowaniem do motywu jasnego/ciemnego i tłem po najechaniu (hover)
        if self.pin_callback:
            pin_icon = "📌" if self.model.is_pinned else "📍"
            # Dla jasnego motywu dajemy ciemniejszy złoty, dla ciemnego jaskrawy żółty. Szary dla wyłączonej.
            pin_color = ("#c29200", "#ffcc00") if self.model.is_pinned else ("#999999", "#666666")
            hover_bg = ("#e0e0e0", "#3a3a3a")

            ctk.CTkButton(
                p_frame, text=pin_icon, width=28, height=28, fg_color="transparent",
                hover_color=hover_bg, text_color=pin_color, font=("Helvetica", 16),
                command=lambda: self.pin_callback(self.model)
            ).pack(side="left", padx=(5, 0))

        if self.model.tags:
            ctk.CTkLabel(header, text=" ".join([f"#{t}" for t in self.model.tags]), font=st.FONT_TAGS).grid(row=1,
                                                                                                            column=0,
                                                                                                            columnspan=2,
                                                                                                            sticky="w")

        # ==========================================
        # SEKCJA 1.5: CZAS (Zawsze widoczny)
        # ==========================================
        dl = self.model.days_left
        dl_text, dl_color = "", st.TIME_COLORS["none"]
        if dl is not None:
            if dl < 0:
                dl_color, dl_text = st.TIME_COLORS["overdue"], f"Po terminie ({-dl} dni temu)"
            elif dl == 0:
                dl_color, dl_text = st.TIME_COLORS["today"], "Termin mija DZIŚ!"
            elif dl == 1:
                dl_color, dl_text = st.TIME_COLORS["1_3"], "Został 1 dzień"
            else:
                if dl <= 3:
                    dl_color = st.TIME_COLORS["1_3"]
                elif dl <= 7:
                    dl_color = st.TIME_COLORS["4_7"]
                elif dl <= 14:
                    dl_color = st.TIME_COLORS["8_14"]
                else:
                    dl_color = st.TIME_COLORS["15_plus"]
                dl_text = f"Zostało: {dl} dni ({self.model.deadline})"

        if dl_text: ctk.CTkLabel(self, text=f"⏱️ {dl_text}", font=st.FONT_TAGS, text_color=dl_color).grid(row=1,
                                                                                                          column=0,
                                                                                                          sticky="w",
                                                                                                          padx=10,
                                                                                                          pady=(0, 5))

        # ==========================================
        # SEKCJA 2: ZAWARTOŚĆ (Tylko w trybie Pełnym!)
        # ==========================================
        if not self.is_compact:
            content_frame = ctk.CTkFrame(self, fg_color="transparent")
            content_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

            if self.model.content.get("text"):
                ctk.CTkLabel(content_frame, text=self.model.content.get("text"), wraplength=250, justify="left").grid(
                    row=0, column=0, sticky="w", pady=(0, 10))

            todos = self.model.content.get("todos", [])
            if todos:
                for index, todo in enumerate(todos):
                    stan_zadania = ctk.BooleanVar(value=todo.get("is_done"))
                    checkbox_state = "disabled" if self.model.is_completed else "normal"
                    checkbox_widget = ctk.CTkCheckBox(content_frame, text=todo["task"], variable=stan_zadania,
                                                      state=checkbox_state)
                    if todo.get("is_done"): checkbox_widget.configure(text_color="gray")

                    def on_checkbox_click(t=todo, var=stan_zadania, cb=checkbox_widget):
                        t["is_done"] = var.get()
                        cb.configure(text_color="gray" if var.get() else ["black", "#DCE4EE"])
                        if self.save_callback: self.save_callback()

                    checkbox_widget.configure(command=on_checkbox_click)
                    checkbox_widget.grid(row=index + 1, column=0, sticky="w", pady=2)

        #==========================================
        # SEKCJA 3: AKCJE (Zawsze widoczne na dole)
        # ==========================================
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_pad_y = (10, 10) if self.is_compact else (0, 10)
        action_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=action_pad_y)
        btn_font = ("Helvetica", 11)

        # NOWE: Przycisk otwierający Workflow (jeśli włączone w modelu i nieukończone)
        if self.model.has_workflow and not self.model.is_completed and self.open_workflow_callback:
            ctk.CTkButton(action_frame, text="🗺️ Workflow", width=80, font=btn_font, fg_color="#1f538d",
                          command=lambda: self.open_workflow_callback(self.model)).pack(side="left", padx=(2, 10))

        if self.model.is_completed:
            if self.restore_callback: ctk.CTkButton(action_frame, text="⏪ Przywróć", width=70, font=btn_font, fg_color="#d48806", hover_color="#b07004", command=lambda: self.restore_callback(self.model)).pack(side="left", padx=2)
        else:
            if self.edit_callback: ctk.CTkButton(action_frame, text="✏️ Edytuj", width=60, font=btn_font, command=lambda: self.edit_callback(self.model)).pack(side="left", padx=2)
            if self.complete_callback: ctk.CTkButton(action_frame, text="✅ Zrobione", width=70, font=btn_font, fg_color="green", hover_color="darkgreen", command=lambda: self.complete_callback(self.model)).pack(side="left", padx=2)
        if self.delete_callback: ctk.CTkButton(action_frame, text="🗑️ Usuń", width=50, font=btn_font, fg_color="#8b0000", hover_color="#5c0000", command=lambda: self.delete_callback(self.model)).pack(side="right", padx=2)


class TileFormDialog(ctk.CTkToplevel):
    def __init__(self, master, on_save_callback, existing_tile=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_save_callback = on_save_callback
        self.existing_tile = existing_tile

        self.title("Edytuj Kafelek" if self.existing_tile else "Dodaj Nowy Kafelek")
        self.geometry("650x700")
        self.transient(master)
        self.grab_set()
        self.build_form()

    def build_form(self):
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Tytuł:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.title_entry = ctk.CTkEntry(self)
        self.title_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self, text="Priorytet:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.priority_menu = ctk.CTkOptionMenu(self, values=["very-high", "high", "medium", "low", "without"])
        self.priority_menu.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.priority_menu.set("medium")

        self.deadline_var = ctk.BooleanVar(value=False)
        self.deadline_cb = ctk.CTkCheckBox(self, text="Ustaw termin", variable=self.deadline_var,
                                           command=self.toggle_deadline)
        self.deadline_cb.grid(row=2, column=0, padx=10, pady=10, sticky="e")

        self.cal = DateEntry(self, width=12, background='darkblue', foreground='white', borderwidth=2,
                             date_pattern='y-mm-dd', state="disabled")
        self.cal.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        # Wiersz 3
        self.workflow_var = ctk.BooleanVar(value=False)
        self.workflow_cb = ctk.CTkCheckBox(self, text="Aktywuj płótno Workflow dla tego projektu",
                                           variable=self.workflow_var)
        self.workflow_cb.grid(row=3, column=0, columnspan=2, padx=10, pady=5)

        # Wiersz 4 (Przesunięte w dół)
        ctk.CTkLabel(self, text="Tagi:").grid(row=4, column=0, padx=10, pady=10, sticky="e")
        self.tags_entry = ctk.CTkEntry(self, placeholder_text="np. praca, dom")
        self.tags_entry.grid(row=4, column=1, padx=10, pady=10, sticky="ew")

        # Wiersz 5
        ctk.CTkLabel(self, text="Opis:").grid(row=5, column=0, padx=10, pady=10, sticky="ne")
        self.text_box = ctk.CTkTextbox(self, height=80)
        self.text_box.grid(row=5, column=1, padx=10, pady=10, sticky="ew")

        # Wiersz 6
        ctk.CTkLabel(self, text="Zadania:").grid(row=6, column=0, padx=10, pady=10, sticky="ne")
        self.todos_box = ctk.CTkTextbox(self, height=100)
        self.todos_box.grid(row=6, column=1, padx=10, pady=10, sticky="ew")

        # Wiersz 7
        ctk.CTkLabel(self, text="Kolor tła:").grid(row=7, column=0, padx=10, pady=10, sticky="e")
        color_frame = ctk.CTkFrame(self, fg_color="transparent")
        color_frame.grid(row=7, column=1, padx=10, pady=10, sticky="ew")
        color_frame.grid_columnconfigure(0, weight=1)

        self.color_var = ctk.StringVar(value="Domyślny")
        self.color_menu = ctk.CTkOptionMenu(color_frame, values=list(st.CUSTOM_TILE_COLORS.keys()),
                                            variable=self.color_var, command=self.update_color_preview)
        self.color_menu.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.color_preview = ctk.CTkFrame(color_frame, width=30, height=30, corner_radius=5, border_width=1,
                                          border_color="gray")
        self.color_preview.grid(row=0, column=1)
        self.update_color_preview("Domyślny")

        # Wiersz 8
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=8, column=0, columnspan=2, pady=20)
        ctk.CTkButton(btn_frame, text="Zapisz", command=self.save_data).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Anuluj", command=self.destroy, fg_color="gray").pack(side="left", padx=10)

        if self.existing_tile:
            self.title_entry.insert(0, self.existing_tile.title)
            self.priority_menu.set(self.existing_tile.priority)
            if self.existing_tile.deadline:
                self.deadline_cb.select()
                self.cal.configure(state="normal")
                self.cal.set_date(datetime.strptime(self.existing_tile.deadline, "%Y-%m-%d").date())

            # Wypełnienie zaznaczenia Workflow
            if self.existing_tile.has_workflow:
                self.workflow_cb.select()

            if self.existing_tile.tags: self.tags_entry.insert(0, ", ".join(self.existing_tile.tags))
            if self.existing_tile.content.get("text"): self.text_box.insert("0.0",
                                                                            self.existing_tile.content.get("text"))
            todos = self.existing_tile.content.get("todos", [])
            if todos: self.todos_box.insert("0.0", "\n".join([t["task"] for t in todos]))

            if self.existing_tile.color:
                for name, val in st.CUSTOM_TILE_COLORS.items():
                    if val and tuple(val) == tuple(self.existing_tile.color):
                        self.color_var.set(name)
                        self.update_color_preview(name)
                        break

    def update_color_preview(self, selected_color_name):
        """Aktualizuje kwadracik obok listy na podstawie wybranego koloru"""
        color_val = st.CUSTOM_TILE_COLORS.get(selected_color_name)
        if color_val is None:
            self.color_preview.configure(fg_color=("white", "gray15"))  # Symulacja "Domyślnego"
        else:
            self.color_preview.configure(fg_color=color_val)

    def toggle_deadline(self):
        self.cal.configure(state="normal" if self.deadline_var.get() else "disabled")

    def save_data(self):
        title = self.title_entry.get().strip()
        if not title: return

        deadline = self.cal.get_date().strftime("%Y-%m-%d") if self.deadline_var.get() else None
        tags_raw = self.tags_entry.get()
        tags = [t.strip() for t in tags_raw.split(",")] if tags_raw else []
        desc_text = self.text_box.get("0.0", "end").strip()
        todos_raw = self.todos_box.get("0.0", "end").strip()
        todos_list = [{"task": line.strip(), "is_done": False} for line in todos_raw.split("\n") if line.strip()]
        has_workflow = self.workflow_var.get()
        selected_color = st.CUSTOM_TILE_COLORS.get(self.color_var.get())

        content = {"text": desc_text if desc_text else None, "todos": todos_list}

        if self.existing_tile:
            self.existing_tile.title = title
            self.existing_tile.priority = self.priority_menu.get()
            self.existing_tile.deadline = deadline
            self.existing_tile.tags = tags
            self.existing_tile.content = content
            self.existing_tile.color = selected_color
            self.existing_tile.has_workflow = has_workflow
            self.on_save_callback(self.existing_tile)
        else:
            new_tile = ProjectTileModel(
                title=title, tags=tags, priority=self.priority_menu.get(),
                deadline=deadline, content=content, color=selected_color,has_workflow=has_workflow
            )
            self.on_save_callback(new_tile)

        self.destroy()