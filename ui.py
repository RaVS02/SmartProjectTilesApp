import customtkinter as ctk
import settings as st
from models import ProjectTileModel


class ProjectTileWidget(ctk.CTkFrame):
    def __init__(self, master, tile_model, save_callback=None, delete_callback=None, complete_callback=None,
                 edit_callback=None, restore_callback=None, **kwargs):
        self.model = tile_model
        self.save_callback = save_callback
        self.delete_callback = delete_callback
        self.complete_callback = complete_callback
        self.edit_callback = edit_callback
        self.restore_callback = restore_callback

        if self.model.is_completed:
            bg_color = st.COMPLETED_TILE_COLOR
            border_color = "gray"
        else:
            bg_color = self.model.color if self.model.color else st.DEFAULT_TILE_COLOR
            border_color = st.PRIORITY_COLORS.get(self.model.priority, st.DEFAULT_TILE_COLOR)

        super().__init__(master, fg_color=bg_color, border_color=border_color, border_width=2, corner_radius=10,
                         **kwargs)
        self.build_ui()

    def build_ui(self):
        """Metoda dynamicznie budująca wnętrze kafelka z podziałem na sekcje"""

        # ZMIANA: Zmuszamy wiersz 1 (Zawartość) do maksymalnego rozciągania się w pionie.
        # To zepchnie wiersz 2 (Przyciski akcji) na sam dół kafelka!
        self.grid_rowconfigure(1, weight=1)

        # ==========================================
        # SEKCJA 1: NAGŁÓWEK (Tytuł, Priorytet i Tagi)
        # ==========================================
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        self.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(header_frame, text=self.model.title, font=st.FONT_TITLE)
        title_label.grid(row=0, column=0, sticky="w")

        priority_text = st.PRIORITY_LABELS.get(self.model.priority, "Brak")
        priority_label = ctk.CTkLabel(header_frame, text=f"[{priority_text}]", font=st.FONT_TAGS, text_color="gray")
        priority_label.grid(row=0, column=1, sticky="e")

        if self.model.tags:
            tags_text = " ".join([f"#{tag}" for tag in self.model.tags])
            tags_label = ctk.CTkLabel(header_frame, text=tags_text, font=st.FONT_TAGS)
            tags_label.grid(row=1, column=0, columnspan=2, sticky="w")

        # ==========================================
        # SEKCJA 2: ZAWARTOŚĆ (Tekst i Checkboxy)
        # ==========================================
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        # ZMIANA: Zmieniliśmy sticky="ew" na "nsew", aby ramka też rosła w pionie
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))

        if self.model.content.get("text"):
            content_text = ctk.CTkLabel(content_frame, text=self.model.content.get("text"), wraplength=250,
                                        justify="left")
            content_text.grid(row=0, column=0, sticky="w", pady=(0, 10))

        todos = self.model.content.get("todos", [])
        if todos:
            for index, todo in enumerate(todos):
                stan_zadania = ctk.BooleanVar(value=todo.get("is_done"))
                checkbox_state = "disabled" if self.model.is_completed else "normal"

                # Tworzymy widżet na początku bez komendy
                checkbox_widget = ctk.CTkCheckBox(
                    content_frame,
                    text=todo["task"],
                    variable=stan_zadania,
                    state=checkbox_state
                )

                # ZMIANA: Jeśli na start jest zrobione, od razu nadajemy szary kolor
                if todo.get("is_done"):
                    checkbox_widget.configure(text_color="gray")

                # ZMIANA: Zmodyfikowana funkcja kliknięcia z dynamicznym stylem
                def on_checkbox_click(t=todo, var=stan_zadania, cb=checkbox_widget):
                    t["is_done"] = var.get()

                    if var.get():
                        cb.configure(text_color="gray")
                    else:
                        # Przywracamy domyślne kolory czcionki dla trybu jasnego/ciemnego
                        cb.configure(text_color=["black", "#DCE4EE"])

                    if self.save_callback is not None:
                        self.save_callback()

                # Przypinamy komendę do stworzonego wcześniej widżetu
                checkbox_widget.configure(command=on_checkbox_click)
                checkbox_widget.grid(row=index + 1, column=0, sticky="w", pady=2)

        # ==========================================
        # SEKCJA 3: PASEK AKCJI (Przyciski na dole)
        # ==========================================
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))

        btn_font = ("Helvetica", 11)

        if self.model.is_completed:
            if self.restore_callback:
                ctk.CTkButton(action_frame, text="⏪ Przywróć", width=70, font=btn_font, fg_color="#d48806",
                              hover_color="#b07004",
                              command=lambda: self.restore_callback(self.model)).pack(side="left", padx=2)
        else:
            if self.edit_callback:
                ctk.CTkButton(action_frame, text="✏️ Edytuj", width=60, font=btn_font,
                              command=lambda: self.edit_callback(self.model)).pack(side="left", padx=2)

            if self.complete_callback:
                ctk.CTkButton(action_frame, text="✅ Zrobione", width=70, font=btn_font, fg_color="green",
                              hover_color="darkgreen",
                              command=lambda: self.complete_callback(self.model)).pack(side="left", padx=2)

        if self.delete_callback:
            ctk.CTkButton(action_frame, text="🗑️ Usuń", width=50, font=btn_font, fg_color="#8b0000",
                          hover_color="#5c0000",
                          command=lambda: self.delete_callback(self.model)).pack(side="right", padx=2)


class TileFormDialog(ctk.CTkToplevel):
    def __init__(self, master, on_save_callback, existing_tile=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_save_callback = on_save_callback
        self.existing_tile = existing_tile

        if self.existing_tile:
            self.title("Edytuj Kafelek")
        else:
            self.title("Dodaj Nowy Kafelek")

        self.geometry("450x600")
        self.transient(master)
        self.grab_set()
        self.build_form()

    def build_form(self):
        self.grid_columnconfigure(1, weight=1)

        # 1. Tytuł
        ctk.CTkLabel(self, text="Tytuł:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.title_entry = ctk.CTkEntry(self)
        self.title_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # 2. Priorytet
        ctk.CTkLabel(self, text="Priorytet:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.priority_menu = ctk.CTkOptionMenu(
            self,
            values=["very-high", "high", "medium", "low", "without"]
        )
        self.priority_menu.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.priority_menu.set("medium")

        # 3. Tagi
        ctk.CTkLabel(self, text="Tagi (po przecinku):").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.tags_entry = ctk.CTkEntry(self, placeholder_text="np. praca, dom, pilne")
        self.tags_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        # 4. Opis
        ctk.CTkLabel(self, text="Opis:").grid(row=3, column=0, padx=10, pady=10, sticky="ne")
        self.text_box = ctk.CTkTextbox(self, height=80)
        self.text_box.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

        # 5. Zadania
        ctk.CTkLabel(self, text="Zadania:\n(każde w nowej linii)").grid(row=4, column=0, padx=10, pady=10, sticky="ne")
        self.todos_box = ctk.CTkTextbox(self, height=100)
        self.todos_box.grid(row=4, column=1, padx=10, pady=10, sticky="ew")

        # 6. Przyciski Zapisu/Anulowania
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)

        ctk.CTkButton(btn_frame, text="Zapisz", command=self.save_data).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Anuluj", command=self.destroy, fg_color="gray").pack(side="left", padx=10)

        # DODATEK: Jeśli edytujemy, wypełniamy pola formularza
        if self.existing_tile:
            self.title_entry.insert(0, self.existing_tile.title)
            self.priority_menu.set(self.existing_tile.priority)

            if self.existing_tile.tags:
                self.tags_entry.insert(0, ", ".join(self.existing_tile.tags))

            if self.existing_tile.content.get("text"):
                self.text_box.insert("0.0", self.existing_tile.content.get("text"))

            todos = self.existing_tile.content.get("todos", [])
            if todos:
                todos_text = "\n".join([t["task"] for t in todos])
                self.todos_box.insert("0.0", todos_text)

    def save_data(self):
        title = self.title_entry.get().strip()
        if not title: return

        tags_raw = self.tags_entry.get()
        tags = [t.strip() for t in tags_raw.split(",")] if tags_raw else []

        desc_text = self.text_box.get("0.0", "end").strip()
        todos_raw = self.todos_box.get("0.0", "end").strip()

        todos_list = []
        if todos_raw:
            for line in todos_raw.split("\n"):
                if line.strip():
                    todos_list.append({"task": line.strip(), "is_done": False})

        content = {"text": desc_text if desc_text else None, "todos": todos_list}

        if self.existing_tile:
            self.existing_tile.title = title
            self.existing_tile.priority = self.priority_menu.get()
            self.existing_tile.tags = tags
            self.existing_tile.content = content
            self.on_save_callback(self.existing_tile)
        else:
            new_tile = ProjectTileModel(title=title, tags=tags, priority=self.priority_menu.get(), content=content)
            self.on_save_callback(new_tile)

        self.destroy()