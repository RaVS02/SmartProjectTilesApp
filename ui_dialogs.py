import customtkinter as ctk
import tkinter as tk
import settings as st
from tkcalendar import DateEntry
from datetime import datetime
from models import ProjectTileModel


def snap(val):
    return round(val / 20) * 20


def get_key(d, val, default):
    for k, v in d.items():
        if v == val: return k
    return default


class ExportDialog(ctk.CTkToplevel):
    def __init__(self, master, on_export_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Opcje Eksportu")
        self.geometry("300x380")
        self.on_export_callback = on_export_callback
        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(self, text="Format pliku:", font=("Helvetica", 12, "bold")).pack(pady=(15, 5))
        self.format_var = ctk.StringVar(value="PNG")
        ctk.CTkOptionMenu(self, values=["PNG", "JPG"], variable=self.format_var).pack(pady=5)

        self.grid_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self, text="Pokaż Siatkę", variable=self.grid_var).pack(pady=10)

        self.minimap_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self, text="Pokaż Minimapę", variable=self.minimap_var).pack(pady=10)

        self.trans_var = ctk.BooleanVar(value=True)
        self.trans_cb = ctk.CTkCheckBox(self, text="Przezroczyste Tło (Tylko PNG)", variable=self.trans_var)
        self.trans_cb.pack(pady=10)

        self.format_var.trace_add("write", self.on_format_change)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="Dalej >", command=self.do_export, fg_color="green",
                      hover_color="darkgreen").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Anuluj", command=self.destroy, fg_color="#8b0000", hover_color="#5c0000").pack(
            side="left", padx=5)

    def on_format_change(self, *args):
        if self.format_var.get() == "JPG":
            self.trans_var.set(False)
            self.trans_cb.configure(state="disabled")
            self.grid_var.set(True)
        else:
            self.trans_cb.configure(state="normal")
            self.trans_var.set(True)
            self.grid_var.set(False)

    def do_export(self):
        self.on_export_callback(self.format_var.get(), self.grid_var.get(), self.minimap_var.get(),
                                self.trans_var.get())
        self.destroy()


class NodeEditDialog(ctk.CTkToplevel):
    def __init__(self, master, node, on_save_callback, on_duplicate_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Właściwości Elementu")
        self.geometry("450x850")
        self.node = node
        self.on_save_callback = on_save_callback
        self.on_duplicate_callback = on_duplicate_callback
        self.original_data = self.node.to_dict()
        self.protocol("WM_DELETE_WINDOW", self.cancel_data)
        self.transient(master)
        self.grab_set()

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(side="bottom", fill="x", pady=10, padx=10)
        ctk.CTkButton(self.btn_frame, text="Zapisz", command=self.save_data, fg_color="green",
                      hover_color="darkgreen").pack(side="left", expand=True, padx=5)
        ctk.CTkButton(self.btn_frame, text="Anuluj", command=self.cancel_data, fg_color="#8b0000",
                      hover_color="#5c0000").pack(side="left", expand=True, padx=5)
        ctk.CTkButton(self.btn_frame, text="📑 Kopiuj", fg_color="#b8860b", hover_color="#8a6508",
                      command=self.duplicate_data).pack(side="left", expand=True, padx=5)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        f_layer = ctk.CTkFrame(self.scroll)
        f_layer.pack(fill="x", pady=5, ipadx=10, ipady=10)
        ctk.CTkLabel(f_layer, text="Zarządzanie Warstwami", font=("Helvetica", 12, "bold")).pack(anchor="w",
                                                                                                 pady=(0, 5))
        btn_layer_frame = ctk.CTkFrame(f_layer, fg_color="transparent")
        btn_layer_frame.pack(fill="x")
        ctk.CTkButton(btn_layer_frame, text="⏫ Na wierzch", command=self.bring_front).pack(side="left", expand=True,
                                                                                           padx=2)
        ctk.CTkButton(btn_layer_frame, text="⏬ Na spód", command=self.send_back).pack(side="left", expand=True, padx=2)

        self.f_type_base = ctk.CTkFrame(self.scroll)
        self.f_type_base.pack(fill="x", pady=5, ipadx=10, ipady=10)
        ctk.CTkLabel(self.f_type_base, text="1. Typ Bloku", font=("Helvetica", 12, "bold")).pack(anchor="w")

        current_type = get_key(st.NODE_TYPES, node.node_type, "Zwykły Blok")
        self.type_var = ctk.StringVar(value=current_type)
        self.type_var.trace_add("write", self.on_type_change)
        ctk.CTkOptionMenu(self.f_type_base, values=list(st.NODE_TYPES.keys()), variable=self.type_var).pack(fill="x",
                                                                                                            pady=5)

        self.f_shape = ctk.CTkFrame(self.scroll, fg_color="transparent")
        ctk.CTkLabel(self.f_shape, text="Kształt:").pack(anchor="w")
        current_shape = get_key(st.NODE_SHAPES, node.shape, "Prostokąt zaokrąglony")
        self.shape_var = ctk.StringVar(value=current_shape)
        self.shape_var.trace_add("write", self.update_live)
        ctk.CTkOptionMenu(self.f_shape, values=list(st.NODE_SHAPES.keys()), variable=self.shape_var).pack(fill="x",
                                                                                                          pady=2)

        self.f_text = ctk.CTkFrame(self.scroll)
        self.f_text.pack(fill="x", pady=5, ipadx=10, ipady=10)
        ctk.CTkLabel(self.f_text, text="2. Zawartość", font=("Helvetica", 12, "bold")).pack(anchor="w")
        ctk.CTkLabel(self.f_text, text="Nagłówek (Zostaw puste dla braku):").pack(anchor="w", pady=(5, 0))
        self.header_var = ctk.StringVar(value=node.header)
        self.header_var.trace_add("write", self.update_live)
        ctk.CTkEntry(self.f_text, textvariable=self.header_var).pack(fill="x", pady=2)
        ctk.CTkLabel(self.f_text, text="Tekst główny:").pack(anchor="w", pady=(5, 0))
        self.text_box = ctk.CTkTextbox(self.f_text, height=80)
        self.text_box.pack(fill="x", pady=2)
        self.text_box.insert("0.0", node.text)
        self.text_box.bind("<KeyRelease>", self.update_live)

        self.f_proj = ctk.CTkFrame(self.scroll)
        ctk.CTkLabel(self.f_proj, text="3. Dane Projektowe", font=("Helvetica", 12, "bold")).pack(anchor="w",
                                                                                                  pady=(10, 0), padx=10)
        pr_frame = ctk.CTkFrame(self.f_proj, fg_color="transparent")
        pr_frame.pack(fill="x", pady=2, padx=10)
        ctk.CTkLabel(pr_frame, text="Priorytet:").pack(side="left")
        self.priority_var = ctk.StringVar(value=getattr(node, "priority", "medium"))
        ctk.CTkOptionMenu(pr_frame, values=["very-high", "high", "medium", "low", "without"],
                          variable=self.priority_var, width=120, command=self.update_live).pack(side="right")

        cal_frame = ctk.CTkFrame(self.f_proj, fg_color="transparent")
        cal_frame.pack(fill="x", pady=5, padx=10)
        self.deadline_var = ctk.BooleanVar(value=bool(getattr(node, "deadline", "")))
        self.deadline_cb = ctk.CTkCheckBox(cal_frame, text="Ustaw termin", variable=self.deadline_var,
                                           command=self.toggle_deadline)
        self.deadline_cb.pack(side="left")

        self.cal = DateEntry(cal_frame, width=12, background='darkblue', foreground='white', borderwidth=2,
                             date_pattern='y-mm-dd', state="normal" if self.deadline_var.get() else "disabled")
        if getattr(node, "deadline", ""):
            try:
                self.cal.set_date(datetime.strptime(node.deadline, "%Y-%m-%d").date())
            except ValueError:
                pass
        self.cal.bind("<<DateEntrySelected>>", self.update_live)
        self.cal.pack(side="right")

        self.show_days_var = ctk.BooleanVar(value=getattr(node, "show_days_left", False))
        ctk.CTkCheckBox(self.f_proj, text="Pokazuj ile dni zostało", variable=self.show_days_var,
                        command=self.update_live).pack(anchor="w", pady=(2, 5), padx=15)

        tag_frame = ctk.CTkFrame(self.f_proj, fg_color="transparent")
        tag_frame.pack(fill="x", pady=2, padx=10, ipady=10)
        ctk.CTkLabel(tag_frame, text="Tagi:").pack(side="left")
        self.tags_var = ctk.StringVar(value=getattr(node, "tags", ""))
        self.tags_var.trace_add("write", self.update_live)
        ctk.CTkEntry(tag_frame, textvariable=self.tags_var, width=150, placeholder_text="np. dom, bug").pack(
            side="right")

        self.f_color = ctk.CTkFrame(self.scroll)
        ctk.CTkLabel(self.f_color, text="4. Kolory Elementu", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=10,
                                                                                                   pady=(10, 0))

        bg_frame = ctk.CTkFrame(self.f_color, fg_color="transparent")
        bg_frame.pack(fill="x", pady=2, padx=10)
        ctk.CTkLabel(bg_frame, text="Kolor Tła:").pack(side="left")
        current_bg = get_key(st.NODE_BG_COLORS, node.color, "Domyślny")
        init_bg_color = st.NODE_BG_COLORS.get(current_bg) or "#1e1e1e"
        self.bg_preview = ctk.CTkFrame(bg_frame, width=20, height=20, corner_radius=3, fg_color=init_bg_color)
        self.bg_preview.pack(side="right", padx=(5, 0))
        self.bg_var = ctk.StringVar(value=current_bg)
        ctk.CTkOptionMenu(bg_frame, values=list(st.NODE_BG_COLORS.keys()), variable=self.bg_var, width=130,
                          command=self.update_bg_preview).pack(side="right")

        border_frame = ctk.CTkFrame(self.f_color, fg_color="transparent")
        border_frame.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(border_frame, text="Kolor Ramki:").pack(side="left")
        current_border = get_key(st.NODE_BORDER_COLORS, getattr(node, "border_color", None), "Domyślny Szary")
        init_border_color = st.NODE_BORDER_COLORS.get(current_border) or "#666666"
        self.border_preview = ctk.CTkFrame(border_frame, width=20, height=20, corner_radius=3,
                                           fg_color=init_border_color)
        self.border_preview.pack(side="right", padx=(5, 0))
        self.border_var = ctk.StringVar(value=current_border)
        ctk.CTkOptionMenu(border_frame, values=list(st.NODE_BORDER_COLORS.keys()), variable=self.border_var, width=130,
                          command=self.update_border_preview).pack(side="right")

        self.f_typo = ctk.CTkFrame(self.scroll)
        self.f_typo.pack(fill="x", pady=5, ipadx=10, ipady=10)
        ctk.CTkLabel(self.f_typo, text="5. Typografia", font=("Helvetica", 12, "bold")).pack(anchor="w")

        row1 = ctk.CTkFrame(self.f_typo, fg_color="transparent")
        row1.pack(fill="x", pady=2)
        ctk.CTkLabel(row1, text="Czcionka:").pack(side="left")
        self.font_family_var = ctk.StringVar(value=getattr(node, "font_family", "Helvetica"))
        ctk.CTkOptionMenu(row1, values=st.CANVAS_FONT_FAMILIES, variable=self.font_family_var, width=120,
                          command=self.update_live).pack(side="right")

        row2 = ctk.CTkFrame(self.f_typo, fg_color="transparent")
        row2.pack(fill="x", pady=2)
        ctk.CTkLabel(row2, text="Wielkość:").pack(side="left")
        self.font_size_var = ctk.StringVar(value=str(getattr(node, "font_size", 12)))
        ctk.CTkOptionMenu(row2, values=st.CANVAS_FONT_SIZES, variable=self.font_size_var, width=120,
                          command=self.update_live).pack(side="right")

        row3 = ctk.CTkFrame(self.f_typo, fg_color="transparent")
        row3.pack(fill="x", pady=2)
        ctk.CTkLabel(row3, text="Kolor Tekstu:").pack(side="left")
        curr_fc = get_key(st.CANVAS_FONT_COLORS, getattr(node, "font_color", None), "Domyślny")
        self.font_color_var = ctk.StringVar(value=curr_fc)
        ctk.CTkOptionMenu(row3, values=list(st.CANVAS_FONT_COLORS.keys()), variable=self.font_color_var, width=120,
                          command=self.update_live).pack(side="right")

        f_dim = ctk.CTkFrame(self.scroll)
        f_dim.pack(fill="x", pady=5, ipadx=10, ipady=10)
        ctk.CTkLabel(f_dim, text="6. Wymiary", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 5))
        dim_inner = ctk.CTkFrame(f_dim, fg_color="transparent")
        dim_inner.pack(fill="x")
        ctk.CTkLabel(dim_inner, text="Szer:").pack(side="left", padx=(0, 5))
        self.width_var = ctk.StringVar(value=str(int(node.width)))
        self.width_var.trace_add("write", self.update_live)
        ctk.CTkEntry(dim_inner, textvariable=self.width_var, width=60, justify="center").pack(side="left", padx=5)

        ctk.CTkLabel(dim_inner, text="Wys:").pack(side="left", padx=(10, 5))
        self.height_var = ctk.StringVar(value=str(int(node.height)))
        self.height_var.trace_add("write", self.update_live)
        ctk.CTkEntry(dim_inner, textvariable=self.height_var, width=60, justify="center").pack(side="left")

        self.on_type_change()

    def on_type_change(self, *args):
        ntype = st.NODE_TYPES.get(self.type_var.get())
        if ntype == "project":
            self.f_shape.pack_forget()
            self.f_color.pack(fill="x", pady=5, ipadx=10, ipady=10)
            self.f_proj.pack(after=self.f_text, fill="x", pady=5, ipadx=10, ipady=10)
        elif ntype == "text":
            self.f_shape.pack_forget()
            self.f_proj.pack_forget()
            self.f_color.pack_forget()
        else:
            self.f_proj.pack_forget()
            self.f_color.pack(fill="x", pady=5, ipadx=10, ipady=10)
            self.f_shape.pack(after=self.f_type_base, fill="x", pady=(0, 5), padx=10)
        self.update_live()

    def bring_front(self):
        self.node.bring_to_front()
        self.master.nodes[self.node.id] = self.master.nodes.pop(self.node.id)
        self.master.mark_unsaved()

    def send_back(self):
        self.node.send_to_back()
        new_nodes = {self.node.id: self.master.nodes.pop(self.node.id)}
        new_nodes.update(self.master.nodes)
        self.master.nodes = new_nodes
        self.master.mark_unsaved()

    def toggle_deadline(self):
        self.cal.configure(state="normal" if self.deadline_var.get() else "disabled")
        self.update_live()

    def update_bg_preview(self, choice):
        color = st.NODE_BG_COLORS.get(choice)
        self.bg_preview.configure(fg_color=color if color else "#1e1e1e")
        self.update_live()

    def update_border_preview(self, choice):
        color = st.NODE_BORDER_COLORS.get(choice)
        self.border_preview.configure(fg_color=color if color else "#666666")
        self.update_live()

    def get_current_data(self):
        deadline = self.cal.get_date().strftime("%Y-%m-%d") if self.deadline_var.get() else ""
        ntype = st.NODE_TYPES.get(self.type_var.get())
        shape = "rect" if ntype in ["project", "text"] else st.NODE_SHAPES.get(self.shape_var.get())
        try:
            new_w = snap(int(self.width_var.get()))
            new_h = snap(int(self.height_var.get()))
            f_size = int(self.font_size_var.get())
        except ValueError:
            new_w, new_h = self.node.width, self.node.height
            f_size = 12

        return {
            "text": self.text_box.get("0.0", "end").strip(),
            "header": self.header_var.get(),
            "shape": shape,
            "node_type": ntype,
            "color": st.NODE_BG_COLORS.get(self.bg_var.get()),
            "border_color": st.NODE_BORDER_COLORS.get(self.border_var.get()),
            "width": new_w, "height": new_h,
            "priority": self.priority_var.get(), "deadline": deadline, "tags": self.tags_var.get(),
            "show_days_left": self.show_days_var.get(),
            "font_family": self.font_family_var.get(),
            "font_size": f_size,
            "font_color": st.CANVAS_FONT_COLORS.get(self.font_color_var.get())
        }

    def update_live(self, *args):
        if not hasattr(self, "width_var") or not hasattr(self, "font_size_var"): return
        self.node.update_properties(self.get_current_data())
        for edge in self.master.edges.values():
            if edge.source == self.node or edge.target == self.node:
                edge.update_position()
        self.master.draw_group_selection()
        self.master.mark_unsaved()
        self.master.update_minimap()

    def cancel_data(self):
        self.node.update_properties(self.original_data)
        for edge in self.master.edges.values():
            if edge.source == self.node or edge.target == self.node:
                edge.update_position()
        self.master.draw_group_selection()
        self.master.update_minimap()
        self.destroy()

    def save_data(self):
        self.on_save_callback(self.node, self.get_current_data())
        self.destroy()

    def duplicate_data(self):
        self.node.update_properties(self.original_data)
        for edge in self.master.edges.values():
            if edge.source == self.node or edge.target == self.node: edge.update_position()
        self.on_duplicate_callback(self.node)
        self.destroy()


class EdgeEditDialog(ctk.CTkToplevel):
    def __init__(self, master, edge, on_save_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Właściwości Linii")
        self.geometry("300x480")
        self.edge = edge
        self.on_save_callback = on_save_callback

        self.original_data = self.edge.to_dict()
        self.protocol("WM_DELETE_WINDOW", self.cancel_data)
        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(self, text="Etykieta (Tekst na linii):").pack(pady=(15, 5))
        self.label_var = ctk.StringVar(value=getattr(edge, "label", ""))
        self.label_var.trace_add("write", self.update_live)
        ctk.CTkEntry(self, textvariable=self.label_var, width=200).pack(pady=5)

        ctk.CTkLabel(self, text="Typ strzałki:").pack(pady=(15, 5))
        current_dir = get_key(st.EDGE_DIRECTIONS, edge.direction, "A ➔ B (Domyślny)")
        self.dir_var = ctk.StringVar(value=current_dir)
        ctk.CTkOptionMenu(self, values=list(st.EDGE_DIRECTIONS.keys()), variable=self.dir_var,
                          command=self.update_live).pack(pady=5)

        ctk.CTkLabel(self, text="Kolor Linii:").pack(pady=(15, 5))
        current_ecolor = get_key(st.EDGE_COLORS, edge.color, "Szary (Domyślny)")
        self.color_var = ctk.StringVar(value=current_ecolor)
        ctk.CTkOptionMenu(self, values=list(st.EDGE_COLORS.keys()), variable=self.color_var,
                          command=self.update_live).pack(pady=5)

        ctk.CTkLabel(self, text="Grubość Linii:").pack(pady=(15, 5))
        self.width_slider = ctk.CTkSlider(self, from_=1, to=8, number_of_steps=7, command=self.update_live)
        self.width_slider.set(edge.line_width)
        self.width_slider.pack(pady=5)

        self.dashed_var = ctk.BooleanVar(value=edge.dashed)
        ctk.CTkCheckBox(self, text="Linia Przerywana", variable=self.dashed_var, command=self.update_live).pack(pady=15)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="Zapisz", command=self.save_data, width=100, fg_color="green",
                      hover_color="darkgreen").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Anuluj", command=self.cancel_data, width=100, fg_color="#8b0000",
                      hover_color="#5c0000").pack(side="left", padx=5)

    def update_live(self, *args):
        if not hasattr(self, "width_slider"): return
        new_dir = st.EDGE_DIRECTIONS.get(self.dir_var.get())
        new_color = st.EDGE_COLORS.get(self.color_var.get())
        new_dashed = self.dashed_var.get()
        new_w = int(self.width_slider.get())
        new_label = self.label_var.get()
        self.edge.update_properties(new_dir, new_color, new_dashed, new_w, new_label)
        self.master.mark_unsaved()
        self.master.update_minimap()

    def cancel_data(self):
        self.edge.update_properties(
            self.original_data["direction"], self.original_data["color"],
            self.original_data["dashed"], self.original_data.get("line_width", 2),
            self.original_data.get("label", "")
        )
        self.master.update_minimap()
        self.destroy()

    def save_data(self):
        new_dir = st.EDGE_DIRECTIONS.get(self.dir_var.get())
        new_color = st.EDGE_COLORS.get(self.color_var.get())
        new_dashed = self.dashed_var.get()
        new_w = int(self.width_slider.get())
        new_label = self.label_var.get()
        self.on_save_callback(self.edge, new_dir, new_color, new_dashed, new_w, new_label)
        self.destroy()


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

        self.workflow_var = ctk.BooleanVar(value=False)
        self.workflow_cb = ctk.CTkCheckBox(self, text="Aktywuj płótno Workflow dla tego projektu",
                                           variable=self.workflow_var)
        self.workflow_cb.grid(row=3, column=0, columnspan=2, padx=10, pady=5)

        ctk.CTkLabel(self, text="Tagi:").grid(row=4, column=0, padx=10, pady=10, sticky="e")
        self.tags_entry = ctk.CTkEntry(self, placeholder_text="np. praca, dom")
        self.tags_entry.grid(row=4, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self, text="Opis:").grid(row=5, column=0, padx=10, pady=10, sticky="ne")
        self.text_box = ctk.CTkTextbox(self, height=80)
        self.text_box.grid(row=5, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self, text="Zadania:").grid(row=6, column=0, padx=10, pady=10, sticky="ne")
        self.todos_box = ctk.CTkTextbox(self, height=100)
        self.todos_box.grid(row=6, column=1, padx=10, pady=10, sticky="ew")

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
            if self.existing_tile.has_workflow: self.workflow_cb.select()
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
        color_val = st.CUSTOM_TILE_COLORS.get(selected_color_name)
        if color_val is None:
            self.color_preview.configure(fg_color=("white", "gray15"))
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
                deadline=deadline, content=content, color=selected_color, has_workflow=has_workflow
            )
            self.on_save_callback(new_tile)

        self.destroy()