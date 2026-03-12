import customtkinter as ctk
import settings as st

class ProjectTileWidget(ctk.CTkFrame):
    def __init__(self, master, tile_model, is_compact=False, color_style="Kolorowe Tło",
                 save_callback=None, delete_callback=None, complete_callback=None,
                 edit_callback=None, restore_callback=None, pin_callback=None,
                 open_workflow_callback=None, title_wrap=200, **kwargs):
        self.model = tile_model
        self.is_compact = is_compact
        self.color_style = color_style
        self.title_wrap = title_wrap

        self.save_callback, self.delete_callback, self.complete_callback = save_callback, delete_callback, complete_callback
        self.edit_callback, self.restore_callback, self.pin_callback = edit_callback, restore_callback, pin_callback
        self.open_workflow_callback = open_workflow_callback

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
            else:
                bg_color, border_color = st.DEFAULT_TILE_COLOR, "gray"

        super().__init__(master, fg_color=bg_color, border_color=border_color, border_width=2, corner_radius=10, **kwargs)
        self.build_ui()

    def build_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        title_label = ctk.CTkLabel(header, text=self.model.title, font=st.FONT_TITLE, justify="left", wraplength=self.title_wrap)
        title_label.grid(row=0, column=0, sticky="w")

        p_frame = ctk.CTkFrame(header, fg_color="transparent")
        p_frame.grid(row=0, column=1, sticky="e")

        dot_color = st.PRIORITY_COLORS.get(self.model.priority, "gray")
        ctk.CTkFrame(p_frame, width=10, height=10, corner_radius=5, fg_color=dot_color).pack(side="left", padx=5)

        priority_text = st.PRIORITY_LABELS.get(self.model.priority, "")
        ctk.CTkLabel(p_frame, text=priority_text, font=("Helvetica", 11, "bold"), text_color=("#444444", "#cccccc")).pack(side="left")

        if self.pin_callback:
            pin_icon = "📌" if self.model.is_pinned else "📍"
            pin_color = ("#c29200", "#ffcc00") if self.model.is_pinned else ("#999999", "#666666")
            hover_bg = ("#e0e0e0", "#3a3a3a")
            ctk.CTkButton(
                p_frame, text=pin_icon, width=28, height=28, fg_color="transparent",
                hover_color=hover_bg, text_color=pin_color, font=("Helvetica", 16),
                command=lambda: self.pin_callback(self.model)
            ).pack(side="left", padx=(5, 0))

        if self.model.tags:
            ctk.CTkLabel(header, text=" ".join([f"#{t}" for t in self.model.tags]), font=st.FONT_TAGS).grid(row=1, column=0, columnspan=2, sticky="w")

        dl = self.model.days_left
        dl_text, dl_color = "", st.TIME_COLORS["none"]
        if dl is not None:
            if dl < 0: dl_color, dl_text = st.TIME_COLORS["overdue"], f"Po terminie ({-dl} dni temu)"
            elif dl == 0: dl_color, dl_text = st.TIME_COLORS["today"], "Termin mija DZIŚ!"
            elif dl == 1: dl_color, dl_text = st.TIME_COLORS["1_3"], "Został 1 dzień"
            else:
                if dl <= 3: dl_color = st.TIME_COLORS["1_3"]
                elif dl <= 7: dl_color = st.TIME_COLORS["4_7"]
                elif dl <= 14: dl_color = st.TIME_COLORS["8_14"]
                else: dl_color = st.TIME_COLORS["15_plus"]
                dl_text = f"Zostało: {dl} dni ({self.model.deadline})"

        if dl_text: ctk.CTkLabel(self, text=f"⏱️ {dl_text}", font=st.FONT_TAGS, text_color=dl_color).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 5))

        if not self.is_compact:
            content_frame = ctk.CTkFrame(self, fg_color="transparent")
            content_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

            if self.model.content.get("text"):
                ctk.CTkLabel(content_frame, text=self.model.content.get("text"), wraplength=250, justify="left").grid(row=0, column=0, sticky="w", pady=(0, 10))

            todos = self.model.content.get("todos", [])
            if todos:
                for index, todo in enumerate(todos):
                    stan_zadania = ctk.BooleanVar(value=todo.get("is_done"))
                    checkbox_state = "disabled" if self.model.is_completed else "normal"
                    checkbox_widget = ctk.CTkCheckBox(content_frame, text=todo["task"], variable=stan_zadania, state=checkbox_state)
                    if todo.get("is_done"): checkbox_widget.configure(text_color="gray")

                    def on_checkbox_click(t=todo, var=stan_zadania, cb=checkbox_widget):
                        t["is_done"] = var.get()
                        cb.configure(text_color="gray" if var.get() else ["black", "#DCE4EE"])
                        if self.save_callback: self.save_callback()

                    checkbox_widget.configure(command=on_checkbox_click)
                    checkbox_widget.grid(row=index + 1, column=0, sticky="w", pady=2)

        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_pad_y = (10, 10) if self.is_compact else (0, 10)
        action_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=action_pad_y)
        btn_font = ("Helvetica", 11)

        if self.model.has_workflow and not self.model.is_completed and self.open_workflow_callback:
            ctk.CTkButton(action_frame, text="🗺️ Workflow", width=80, font=btn_font, fg_color="#1f538d", command=lambda: self.open_workflow_callback(self.model)).pack(side="left", padx=(2, 10))

        if self.model.is_completed:
            if self.restore_callback: ctk.CTkButton(action_frame, text="⏪ Przywróć", width=70, font=btn_font, fg_color="#d48806", hover_color="#b07004", command=lambda: self.restore_callback(self.model)).pack(side="left", padx=2)
        else:
            if self.edit_callback: ctk.CTkButton(action_frame, text="✏️ Edytuj", width=60, font=btn_font, command=lambda: self.edit_callback(self.model)).pack(side="left", padx=2)
            if self.complete_callback: ctk.CTkButton(action_frame, text="✅ Zrobione", width=70, font=btn_font, fg_color="green", hover_color="darkgreen", command=lambda: self.complete_callback(self.model)).pack(side="left", padx=2)
        if self.delete_callback: ctk.CTkButton(action_frame, text="🗑️ Usuń", width=50, font=btn_font, fg_color="#8b0000", hover_color="#5c0000", command=lambda: self.delete_callback(self.model)).pack(side="right", padx=2)