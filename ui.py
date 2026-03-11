import customtkinter as ctk
import settings as st
from models import ProjectTileModel
from tkcalendar import DateEntry  # <--- NOWY IMPORT
from datetime import datetime


class ProjectTileWidget(ctk.CTkFrame):
    def __init__(self, master, tile_model, save_callback=None, delete_callback=None, complete_callback=None,
                 edit_callback=None, restore_callback=None, **kwargs):
        self.model = tile_model
        self.save_callback = save_callback
        self.delete_callback = delete_callback
        self.complete_callback = complete_callback
        self.edit_callback = edit_callback
        self.restore_callback = restore_callback

        # LOGIKA RAMKI SUMARYCZNEJ
        total_weight = self.model.total_weight
        if self.model.is_completed:
            bg_color = st.COMPLETED_TILE_COLOR
            border_color = "gray"
        else:
            bg_color = self.model.color if self.model.color else st.DEFAULT_TILE_COLOR
            # Pobieramy kolor ramki na podstawie wagi sumarycznej (domyślnie szary, gdyby wyszło poza skalę)
            border_color = st.SUMMATIVE_COLORS.get(total_weight, st.DEFAULT_TILE_COLOR)

        super().__init__(master, fg_color=bg_color, border_color=border_color, border_width=2, corner_radius=10,
                         **kwargs)
        self.build_ui()

    def build_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # NAGŁÓWEK - NAPRAWA (Title po lewej, Priority po prawej)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        header.grid_columnconfigure(0, weight=1)  # Tytuł zajmuje wolne miejsce
        header.grid_columnconfigure(1, weight=0)  # Kontener priorytetu trzyma się prawej

        ctk.CTkLabel(header, text=self.model.title, font=st.FONT_TITLE).grid(row=0, column=0, sticky="w")

        # Kontener kropki i tekstu priorytetu
        p_frame = ctk.CTkFrame(header, fg_color="transparent")
        p_frame.grid(row=0, column=1, sticky="e")

        dot_color = st.PRIORITY_COLORS.get(self.model.priority, "gray")
        ctk.CTkFrame(p_frame, width=10, height=10, corner_radius=5, fg_color=dot_color).pack(side="left", padx=5)
        ctk.CTkLabel(p_frame, text=st.PRIORITY_LABELS.get(self.model.priority, ""), font=st.FONT_TAGS,
                     text_color="gray").pack(side="left")

        if self.model.tags:
            tags_text = " ".join([f"#{tag}" for tag in self.model.tags])
            tags_label = ctk.CTkLabel(header, text=tags_text, font=st.FONT_TAGS)
            tags_label.grid(row=1, column=0, columnspan=3, sticky="w")

        # ==========================================
        # SEKCJA 1.5: DEADLINE (Czas)
        # ==========================================
        dl = self.model.days_left
        dl_text = ""
        dl_color = st.TIME_COLORS["none"]

        if dl is not None:
            if dl < 0:
                dl_color = st.TIME_COLORS["overdue"]
                dl_text = f"Po terminie ({-dl} dni temu)"
            elif dl == 0:
                dl_color = st.TIME_COLORS["today"]
                dl_text = "Termin mija DZIŚ!"
            elif dl == 1:
                dl_color = st.TIME_COLORS["1_3"]
                dl_text = "Został 1 dzień"
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

        if dl_text:
            date_label = ctk.CTkLabel(self, text=f"⏱️ {dl_text}", font=st.FONT_TAGS, text_color=dl_color)
            date_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 5))

        # ==========================================
        # SEKCJA 2: ZAWARTOŚĆ
        # ==========================================
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

        if self.model.content.get("text"):
            content_text = ctk.CTkLabel(content_frame, text=self.model.content.get("text"), wraplength=250,
                                        justify="left")
            content_text.grid(row=0, column=0, sticky="w", pady=(0, 10))

        todos = self.model.content.get("todos", [])
        if todos:
            for index, todo in enumerate(todos):
                stan_zadania = ctk.BooleanVar(value=todo.get("is_done"))
                checkbox_state = "disabled" if self.model.is_completed else "normal"

                checkbox_widget = ctk.CTkCheckBox(content_frame, text=todo["task"], variable=stan_zadania,
                                                  state=checkbox_state)
                if todo.get("is_done"):
                    checkbox_widget.configure(text_color="gray")

                def on_checkbox_click(t=todo, var=stan_zadania, cb=checkbox_widget):
                    t["is_done"] = var.get()
                    cb.configure(text_color="gray" if var.get() else ["black", "#DCE4EE"])
                    if self.save_callback is not None: self.save_callback()

                checkbox_widget.configure(command=on_checkbox_click)
                checkbox_widget.grid(row=index + 1, column=0, sticky="w", pady=2)

        # ==========================================
        # SEKCJA 3: PASEK AKCJI
        # ==========================================
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
        btn_font = ("Helvetica", 11)

        if self.model.is_completed:
            if self.restore_callback:
                ctk.CTkButton(action_frame, text="⏪ Przywróć", width=70, font=btn_font, fg_color="#d48806",
                              hover_color="#b07004", command=lambda: self.restore_callback(self.model)).pack(
                    side="left", padx=2)
        else:
            if self.edit_callback:
                ctk.CTkButton(action_frame, text="✏️ Edytuj", width=60, font=btn_font,
                              command=lambda: self.edit_callback(self.model)).pack(side="left", padx=2)
            if self.complete_callback:
                ctk.CTkButton(action_frame, text="✅ Zrobione", width=70, font=btn_font, fg_color="green",
                              hover_color="darkgreen", command=lambda: self.complete_callback(self.model)).pack(
                    side="left", padx=2)

        if self.delete_callback:
            ctk.CTkButton(action_frame, text="🗑️ Usuń", width=50, font=btn_font, fg_color="#8b0000",
                          hover_color="#5c0000", command=lambda: self.delete_callback(self.model)).pack(side="right",
                                                                                                        padx=2)


class TileFormDialog(ctk.CTkToplevel):
    def __init__(self, master, on_save_callback, existing_tile=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_save_callback = on_save_callback
        self.existing_tile = existing_tile

        self.title("Edytuj Kafelek" if self.existing_tile else "Dodaj Nowy Kafelek")
        self.geometry("450x650")
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

        # --- KALENDARZ (tkcalendar) ---
        self.deadline_var = ctk.BooleanVar(value=False)
        self.deadline_cb = ctk.CTkCheckBox(self, text="Ustaw termin", variable=self.deadline_var,
                                           command=self.toggle_deadline)
        self.deadline_cb.grid(row=2, column=0, padx=10, pady=10, sticky="e")

        self.cal = DateEntry(self, width=12, background='darkblue', foreground='white', borderwidth=2,
                             date_pattern='y-mm-dd', state="disabled")
        self.cal.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(self, text="Tagi:").grid(row=3, column=0, padx=10, pady=10, sticky="e")
        self.tags_entry = ctk.CTkEntry(self, placeholder_text="np. praca, dom")
        self.tags_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self, text="Opis:").grid(row=4, column=0, padx=10, pady=10, sticky="ne")
        self.text_box = ctk.CTkTextbox(self, height=80)
        self.text_box.grid(row=4, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self, text="Zadania:").grid(row=5, column=0, padx=10, pady=10, sticky="ne")
        self.todos_box = ctk.CTkTextbox(self, height=100)
        self.todos_box.grid(row=5, column=1, padx=10, pady=10, sticky="ew")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=6, column=0, columnspan=2, pady=20)
        ctk.CTkButton(btn_frame, text="Zapisz", command=self.save_data).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Anuluj", command=self.destroy, fg_color="gray").pack(side="left", padx=10)

        # Wypełnianie danych przy edycji
        if self.existing_tile:
            self.title_entry.insert(0, self.existing_tile.title)
            self.priority_menu.set(self.existing_tile.priority)
            if self.existing_tile.deadline:
                self.deadline_cb.select()
                self.cal.configure(state="normal")
                self.cal.set_date(datetime.strptime(self.existing_tile.deadline, "%Y-%m-%d").date())
            if self.existing_tile.tags: self.tags_entry.insert(0, ", ".join(self.existing_tile.tags))
            if self.existing_tile.content.get("text"): self.text_box.insert("0.0",
                                                                            self.existing_tile.content.get("text"))
            todos = self.existing_tile.content.get("todos", [])
            if todos: self.todos_box.insert("0.0", "\n".join([t["task"] for t in todos]))

    def toggle_deadline(self):
        """Włącza/wyłącza kalendarz"""
        self.cal.configure(state="normal" if self.deadline_var.get() else "disabled")

    def save_data(self):
        title = self.title_entry.get().strip()
        if not title: return

        # Pobieranie daty, jeśli checkbox zaznaczony
        deadline = self.cal.get_date().strftime("%Y-%m-%d") if self.deadline_var.get() else None

        tags_raw = self.tags_entry.get()
        tags = [t.strip() for t in tags_raw.split(",")] if tags_raw else []

        desc_text = self.text_box.get("0.0", "end").strip()
        todos_raw = self.todos_box.get("0.0", "end").strip()
        todos_list = [{"task": line.strip(), "is_done": False} for line in todos_raw.split("\n") if line.strip()]

        content = {"text": desc_text if desc_text else None, "todos": todos_list}

        if self.existing_tile:
            self.existing_tile.title = title
            self.existing_tile.priority = self.priority_menu.get()
            self.existing_tile.deadline = deadline
            self.existing_tile.tags = tags
            self.existing_tile.content = content
            self.on_save_callback(self.existing_tile)
        else:
            new_tile = ProjectTileModel(title=title, tags=tags, priority=self.priority_menu.get(), deadline=deadline,
                                        content=content)
            self.on_save_callback(new_tile)

        self.destroy()