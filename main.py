import customtkinter as ctk
import settings as st
from models import TileManager, ProjectTileModel
from ui import ProjectTileWidget, TileFormDialog
import math
import tkinter as tk
import uuid
from tkcalendar import DateEntry
from datetime import datetime

try:
    from PIL import ImageGrab

    HAS_PIL = True
except ImportError:
    HAS_PIL = False

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("green")

GRID_SIZE = 20


def snap(val):
    return round(val / GRID_SIZE) * GRID_SIZE


def get_round_rect_points(x1, y1, x2, y2, r=12):
    return [
        x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y1 + r,
        x2, y2 - r, x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1
    ]


# ==========================================
# OKNO OPCJI EKSPORTU
# ==========================================
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
        self.on_export_callback(
            self.format_var.get(),
            self.grid_var.get(),
            self.minimap_var.get(),
            self.trans_var.get()
        )
        self.destroy()


# ==========================================
# OKIENKA EDYCJI KLOCKÓW
# ==========================================
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
        self.node_types = {"Kafelek Projektu (Szczegółowy)": "project", "Zwykły Blok": "block", "Notatka": "note",
                           "Tylko Tekst (Etykieta)": "text"}
        current_type = "Zwykły Blok"
        for k, v in self.node_types.items():
            if v == node.node_type: current_type = k
        self.type_var = ctk.StringVar(value=current_type)
        self.type_var.trace_add("write", self.on_type_change)
        ctk.CTkOptionMenu(self.f_type_base, values=list(self.node_types.keys()), variable=self.type_var).pack(fill="x",
                                                                                                              pady=5)

        self.f_shape = ctk.CTkFrame(self.scroll, fg_color="transparent")
        ctk.CTkLabel(self.f_shape, text="Kształt:").pack(anchor="w")
        self.shapes = {"Prostokąt zaokrąglony": "rect", "Romb (Decyzja)": "diamond", "Elipsa": "oval",
                       "Równoległobok": "parallelogram"}
        current_shape = "Prostokąt zaokrąglony"
        for k, v in self.shapes.items():
            if v == node.shape: current_shape = k
        self.shape_var = ctk.StringVar(value=current_shape)
        self.shape_var.trace_add("write", self.update_live)
        ctk.CTkOptionMenu(self.f_shape, values=list(self.shapes.keys()), variable=self.shape_var).pack(fill="x", pady=2)

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
        self.bg_colors = {"Domyślny": None, "Ciemnoszary": "#2b2b2b", "Jasnoszary": "#4a4a4a",
                          "Kremowy (Notatka)": "#e6c280", "Brązowy (Notatka)": "#b35900"}
        for k, v in st.CUSTOM_TILE_COLORS.items():
            if k != "Domyślny" and v: self.bg_colors[k] = v[1] if isinstance(v, tuple) else v

        self.border_colors = {
            "Domyślny Szary": "#666666", "Czerwony (Krytyczny)": st.PRIORITY_COLORS["very-high"][1],
            "Pomarańczowy (Wysoki)": st.PRIORITY_COLORS["high"][1], "Żółty (Średni)": st.PRIORITY_COLORS["medium"][1],
            "Zielony (Niski)": st.PRIORITY_COLORS["low"][1], "Fioletowy": "#4b0082", "Biały": "#ffffff",
            "Czarny": "#000000"
        }

        bg_frame = ctk.CTkFrame(self.f_color, fg_color="transparent")
        bg_frame.pack(fill="x", pady=2, padx=10)
        ctk.CTkLabel(bg_frame, text="Kolor Tła:").pack(side="left")
        current_bg = "Domyślny"
        for k, v in self.bg_colors.items():
            if v == node.color: current_bg = k
        init_bg_color = self.bg_colors.get(current_bg) or "#1e1e1e"
        self.bg_preview = ctk.CTkFrame(bg_frame, width=20, height=20, corner_radius=3, fg_color=init_bg_color)
        self.bg_preview.pack(side="right", padx=(5, 0))
        self.bg_var = ctk.StringVar(value=current_bg)
        ctk.CTkOptionMenu(bg_frame, values=list(self.bg_colors.keys()), variable=self.bg_var, width=130,
                          command=self.update_bg_preview).pack(side="right")

        border_frame = ctk.CTkFrame(self.f_color, fg_color="transparent")
        border_frame.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(border_frame, text="Kolor Ramki:").pack(side="left")
        current_border = "Domyślny Szary"
        for k, v in self.border_colors.items():
            if v == getattr(node, "border_color", None): current_border = k
        init_border_color = self.border_colors.get(current_border) or "#666666"
        self.border_preview = ctk.CTkFrame(border_frame, width=20, height=20, corner_radius=3,
                                           fg_color=init_border_color)
        self.border_preview.pack(side="right", padx=(5, 0))
        self.border_var = ctk.StringVar(value=current_border)
        ctk.CTkOptionMenu(border_frame, values=list(self.border_colors.keys()), variable=self.border_var, width=130,
                          command=self.update_border_preview).pack(side="right")

        self.f_typo = ctk.CTkFrame(self.scroll)
        self.f_typo.pack(fill="x", pady=5, ipadx=10, ipady=10)
        ctk.CTkLabel(self.f_typo, text="5. Typografia", font=("Helvetica", 12, "bold")).pack(anchor="w")

        row1 = ctk.CTkFrame(self.f_typo, fg_color="transparent")
        row1.pack(fill="x", pady=2)
        ctk.CTkLabel(row1, text="Czcionka:").pack(side="left")
        self.font_family_var = ctk.StringVar(value=getattr(node, "font_family", "Helvetica"))
        ctk.CTkOptionMenu(row1, values=["Helvetica", "Arial", "Times New Roman", "Courier New", "Verdana", "Impact"],
                          variable=self.font_family_var, width=120, command=self.update_live).pack(side="right")

        row2 = ctk.CTkFrame(self.f_typo, fg_color="transparent")
        row2.pack(fill="x", pady=2)
        ctk.CTkLabel(row2, text="Wielkość:").pack(side="left")
        self.font_size_var = ctk.StringVar(value=str(getattr(node, "font_size", 12)))
        ctk.CTkOptionMenu(row2, values=["8", "10", "12", "14", "16", "20", "24", "32", "48"],
                          variable=self.font_size_var, width=120, command=self.update_live).pack(side="right")

        row3 = ctk.CTkFrame(self.f_typo, fg_color="transparent")
        row3.pack(fill="x", pady=2)
        ctk.CTkLabel(row3, text="Kolor Tekstu:").pack(side="left")
        self.font_color_keys = {"Domyślny": None, "Czarny": "#000000", "Biały": "#ffffff", "Czerwony": "#ff4a4a",
                                "Niebieski": "#4da6ff", "Zielony": "#00cc00", "Żółty": "#ffcc00"}
        curr_fc = "Domyślny"
        for k, v in self.font_color_keys.items():
            if v == getattr(node, "font_color", None): curr_fc = k
        self.font_color_var = ctk.StringVar(value=curr_fc)
        ctk.CTkOptionMenu(row3, values=list(self.font_color_keys.keys()), variable=self.font_color_var, width=120,
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
        ntype = self.node_types.get(self.type_var.get())
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
        color = self.bg_colors.get(choice)
        self.bg_preview.configure(fg_color=color if color else "#1e1e1e")
        self.update_live()

    def update_border_preview(self, choice):
        color = self.border_colors.get(choice)
        self.border_preview.configure(fg_color=color if color else "#666666")
        self.update_live()

    def get_current_data(self):
        deadline = self.cal.get_date().strftime("%Y-%m-%d") if self.deadline_var.get() else ""
        ntype = self.node_types.get(self.type_var.get())
        shape = "rect" if ntype in ["project", "text"] else self.shapes.get(self.shape_var.get())
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
            "color": self.bg_colors.get(self.bg_var.get()),
            "border_color": self.border_colors.get(self.border_var.get()),
            "width": new_w, "height": new_h,
            "priority": self.priority_var.get(), "deadline": deadline, "tags": self.tags_var.get(),
            "show_days_left": self.show_days_var.get(),
            "font_family": self.font_family_var.get(),
            "font_size": f_size,
            "font_color": self.font_color_keys.get(self.font_color_var.get())
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
        self.directions = {"A ➔ B (Domyślny)": "last", "A ⬅ B (Odwrotny)": "first", "A ⬌ B (Dwukierunkowy)": "both",
                           "Linia zwykła (Brak)": "none"}
        current_dir = "A ➔ B (Domyślny)"
        for k, v in self.directions.items():
            if v == edge.direction: current_dir = k
        self.dir_var = ctk.StringVar(value=current_dir)
        ctk.CTkOptionMenu(self, values=list(self.directions.keys()), variable=self.dir_var,
                          command=self.update_live).pack(pady=5)

        ctk.CTkLabel(self, text="Kolor Linii:").pack(pady=(15, 5))
        self.edge_colors = {"Szary (Domyślny)": "#888888", "Czerwony (Błąd/Nie)": "#ff4a4a",
                            "Zielony (Sukces/Tak)": "#00cc00", "Niebieski (Informacja)": "#2980b9"}
        current_ecolor = "Szary (Domyślny)"
        for k, v in self.edge_colors.items():
            if v == edge.color: current_ecolor = k
        self.color_var = ctk.StringVar(value=current_ecolor)
        ctk.CTkOptionMenu(self, values=list(self.edge_colors.keys()), variable=self.color_var,
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
        new_dir = self.directions.get(self.dir_var.get())
        new_color = self.edge_colors.get(self.color_var.get())
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
        new_dir = self.directions.get(self.dir_var.get())
        new_color = self.edge_colors.get(self.color_var.get())
        new_dashed = self.dashed_var.get()
        new_w = int(self.width_slider.get())
        new_label = self.label_var.get()
        self.on_save_callback(self.edge, new_dir, new_color, new_dashed, new_w, new_label)
        self.destroy()


# ==========================================
# KLASY PŁÓTNA (CANVAS)
# ==========================================
class CanvasNode:
    def __init__(self, wf, x, y, text, node_type="block", node_id=None, color=None, border_color=None, width=160,
                 height=80, shape="rect", header="", priority="medium", deadline="", tags="", show_days_left=False,
                 group_id=None, font_family="Helvetica", font_size=12, font_color=None):
        self.wf = wf
        self.canvas = wf.canvas
        self.id = node_id if node_id else str(uuid.uuid4())
        self.group_id = group_id

        self.width = snap(width)
        self.height = snap(height)
        self.x = snap(x)
        self.y = snap(y)

        self.text = text
        self.header = header
        self.shape = shape
        self.node_type = node_type
        self.color = color
        self.border_color = border_color
        self.priority = priority
        self.deadline = deadline
        self.tags = tags
        self.show_days_left = show_days_left
        self.font_family = font_family
        self.font_size = font_size
        self.font_color = font_color
        self.selected = False

        self.bg_id = None;
        self.text_id = None;
        self.header_id = None;
        self.handle_id = None
        self.proj_dot_id = None;
        self.proj_date_id = None;
        self.proj_tags_id = None
        self.draw()

    def bring_to_front(self):
        for item in [self.bg_id, self.header_id, self.text_id, self.proj_dot_id, self.proj_tags_id, self.proj_date_id,
                     self.handle_id]:
            if item: self.canvas.tag_raise(item)

    def send_to_back(self):
        for item in [self.handle_id, self.proj_date_id, self.proj_tags_id, self.proj_dot_id, self.text_id,
                     self.header_id, self.bg_id]:
            if item: self.canvas.tag_lower(item)
        for e in self.wf.edges.values():
            self.canvas.tag_lower(e.line_id)
            if e.label_bg_id: self.canvas.tag_lower(e.label_bg_id)
            if e.label_id: self.canvas.tag_lower(e.label_id)
        self.canvas.tag_lower("grid")

    def get_port_point(self, target_x, target_y):
        cx, cy = self.x, self.y
        w, h = self.width / 2 + 4, self.height / 2 + 4
        if self.shape == "diamond": w -= 10; h -= 10
        ports = [(cx, cy - h), (cx, cy + h), (cx - w, cy), (cx + w, cy)]
        best_port = min(ports, key=lambda p: math.hypot(p[0] - target_x, p[1] - target_y))
        return best_port[0], best_port[1]

    def draw(self):
        self.clear_graphics()
        z = self.wf.zoom
        sx, sy = self.x * z, self.y * z
        sw, sh = self.width * z, self.height * z

        x1, y1 = sx - sw / 2, sy - sh / 2
        x2, y2 = sx + sw / 2, sy + sh / 2

        base_f_size = int(self.font_size * z)
        font_style = (self.font_family, max(4, base_f_size), "bold")
        header_font_style = (self.font_family, max(4, int(base_f_size * 0.8)), "bold")

        if self.node_type == "text":
            outline_c = "#ffcc00" if self.selected else ""
            self.bg_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill="", outline=outline_c, dash=(4, 4),
                                                      tags=("node", self.id))
            t_col = self.font_color if self.font_color else "#DCE4EE"
            self.text_id = self.canvas.create_text(sx, sy, text=self.text, fill=t_col, font=font_style, width=sw,
                                                   justify="center", tags=("node", self.id))
            self.handle_id = self.canvas.create_rectangle(x2 - 12 * z, y2 - 12 * z, x2, y2, fill="white",
                                                          outline="#333", tags=("handle", self.id),
                                                          state="normal" if self.selected else "hidden")
            return

        if self.node_type == "project":
            bg = self.color if self.color else "#1e1e1e"
            outline_color = self.border_color if self.border_color else "#666666"
        else:
            bg = self.color if self.color else ("#b35900" if self.node_type == "note" else "#1f538d")
            outline_color = self.border_color if self.border_color else (
                "#e67300" if self.node_type == "note" else "#2980b9")

        outline_color = "#ffcc00" if self.selected else outline_color

        if self.shape == "oval":
            self.bg_id = self.canvas.create_oval(x1, y1, x2, y2, fill=bg, outline=outline_color,
                                                 width=max(1, int(2 * z)), tags=("node", self.id))
        elif self.shape == "diamond":
            pts = [sx, y1, x2, sy, sx, y2, x1, sy]
            self.bg_id = self.canvas.create_polygon(pts, fill=bg, outline=outline_color, width=max(1, int(2 * z)),
                                                    tags=("node", self.id))
        elif self.shape == "parallelogram":
            offset = sw * 0.15
            pts = [x1 + offset, y1, x2, y1, x2 - offset, y2, x1, y2]
            self.bg_id = self.canvas.create_polygon(pts, fill=bg, outline=outline_color, width=max(1, int(2 * z)),
                                                    tags=("node", self.id))
        else:
            pts = get_round_rect_points(x1, y1, x2, y2, r=12 * z)
            self.bg_id = self.canvas.create_polygon(pts, smooth=True, fill=bg, outline=outline_color,
                                                    width=max(1, int(2 * z)), tags=("node", self.id))

        if self.font_color:
            text_color = self.font_color
            header_color = self.font_color
        else:
            text_color = "black" if bg in ["#ffffff", "#e6c280", "#888888"] else "#DCE4EE"
            header_color = "#555555" if bg in ["#ffffff", "#e6c280", "#888888"] else "#dddddd"

        if self.header:
            self.header_id = self.canvas.create_text(sx, sy - sh / 2 + 12 * z, text=self.header, fill=header_color,
                                                     font=header_font_style, width=sw - 20 * z, justify="center",
                                                     tags=("node", self.id))

        if self.node_type == "project":
            title_y = y1 + (25 * z if self.header else 15 * z)
            self.text_id = self.canvas.create_text(x1 + 10 * z, title_y, text=self.text, fill=text_color,
                                                   font=font_style, width=sw - 40 * z, anchor="w",
                                                   tags=("node", self.id))
            dot_c = st.PRIORITY_COLORS.get(self.priority, ("gray", "gray"))[1]
            pr = 4 * z
            px, py = x2 - 15 * z, title_y
            self.proj_dot_id = self.canvas.create_oval(px - pr, py - pr, px + pr, py + pr, fill=dot_c, outline=dot_c,
                                                       tags=("node", self.id))
            if self.tags:
                self.proj_tags_id = self.canvas.create_text(x1 + 10 * z, title_y + 18 * z, text=" ".join(
                    [f"#{t.strip()}" for t in self.tags.split(",")]), fill="#4da6ff",
                                                            font=(self.font_family, max(4, int(base_f_size * 0.7)),
                                                                  "italic"), width=sw - 20 * z, anchor="w",
                                                            tags=("node", self.id))
            if self.deadline:
                dl_color = "#aaaaaa";
                days_text = ""
                try:
                    d_date = datetime.strptime(self.deadline, "%Y-%m-%d").date()
                    dl = (d_date - datetime.now().date()).days
                    if dl < 0:
                        dl_color = st.TIME_COLORS["overdue"][1]; days_text = f" ({-dl} dni po)"
                    elif dl == 0:
                        dl_color = st.TIME_COLORS["today"][1]; days_text = " (Dziś!)"
                    elif dl == 1:
                        dl_color = st.TIME_COLORS["1_3"][1]; days_text = " (jutro)"
                    elif dl <= 3:
                        dl_color = st.TIME_COLORS["1_3"][1]; days_text = f" ({dl} dni)"
                    elif dl <= 14:
                        dl_color = st.TIME_COLORS["8_14"][1]; days_text = f" ({dl} dni)"
                    else:
                        dl_color = st.TIME_COLORS["15_plus"][1]; days_text = f" ({dl} dni)"
                except ValueError:
                    pass
                if not self.show_days_left: days_text = ""
                self.proj_date_id = self.canvas.create_text(x1 + 10 * z, y2 - 15 * z,
                                                            text=f"⏱ {self.deadline}{days_text}", fill=dl_color,
                                                            font=header_font_style, width=sw - 20 * z, anchor="w",
                                                            tags=("node", self.id))
        else:
            self.text_id = self.canvas.create_text(sx, sy + (10 * z if self.header else 0), text=self.text,
                                                   fill=text_color, font=font_style, width=sw - 20 * z,
                                                   justify="center", tags=("node", self.id))

        self.handle_id = self.canvas.create_rectangle(x2 - 12 * z, y2 - 12 * z, x2, y2, fill="white", outline="#333",
                                                      tags=("handle", self.id),
                                                      state="normal" if self.selected else "hidden")

    def clear_graphics(self):
        for item in [self.bg_id, self.text_id, self.header_id, self.handle_id, self.proj_dot_id, self.proj_date_id,
                     self.proj_tags_id]:
            if item: self.canvas.delete(item)

    def move_to(self, x, y):
        self.x = x; self.y = y; self.draw()

    def resize(self, w, h):
        self.width = max(50, w); self.height = max(30, h); self.draw()

    def set_selected(self, state):
        self.selected = state; self.draw()

    def update_properties(self, data):
        self.text = data.get("text", self.text);
        self.header = data.get("header", self.header)
        self.shape = data.get("shape", self.shape);
        self.node_type = data.get("node_type", data.get("type", self.node_type))
        self.color = data.get("color", self.color);
        self.border_color = data.get("border_color", self.border_color)
        self.priority = data.get("priority", "medium");
        self.deadline = data.get("deadline", "")
        self.tags = data.get("tags", "");
        self.show_days_left = data.get("show_days_left", False)
        self.font_family = data.get("font_family", "Helvetica");
        self.font_size = data.get("font_size", 12)
        self.font_color = data.get("font_color", None)
        self.resize(data.get("width", self.width), data.get("height", self.height));
        self.draw()

    def destroy(self):
        self.clear_graphics()

    def to_dict(self):
        return {
            "id": self.id, "x": self.x, "y": self.y, "text": self.text, "header": self.header,
            "type": self.node_type, "shape": self.shape, "color": self.color,
            "border_color": getattr(self, 'border_color', None),
            "width": self.width, "height": self.height, "priority": getattr(self, 'priority', 'medium'),
            "deadline": getattr(self, 'deadline', ''), "tags": getattr(self, 'tags', ''),
            "show_days_left": getattr(self, 'show_days_left', False), "group_id": self.group_id,
            "font_family": self.font_family, "font_size": self.font_size, "font_color": self.font_color
        }


class CanvasEdge:
    def __init__(self, wf, source_node, target_node, edge_id=None, direction="last", color="#888888", dashed=False,
                 waypoints=None, line_width=2, label=""):
        self.wf = wf;
        self.canvas = wf.canvas
        self.id = edge_id if edge_id else str(uuid.uuid4())
        self.source = source_node;
        self.target = target_node
        self.direction = direction;
        self.color = color;
        self.dashed = dashed;
        self.line_width = line_width
        self.label = label
        self.waypoints = waypoints if waypoints else [];
        self.selected = False
        self.arrow_map = {"last": tk.LAST, "first": tk.FIRST, "both": tk.BOTH, "none": tk.NONE}
        self.line_id = None;
        self.handle_ids = [];
        self.label_id = None;
        self.label_bg_id = None
        self.draw()

    def get_closest_segment_index(self, px, py):
        if not self.waypoints: return 0
        pts = [[self.source.x, self.source.y]] + self.waypoints + [[self.target.x, self.target.y]]
        min_dist = float('inf');
        best_idx = 0
        for i in range(len(pts) - 1):
            x1, y1 = pts[i];
            x2, y2 = pts[i + 1]
            l2 = (x2 - x1) ** 2 + (y2 - y1) ** 2
            if l2 == 0:
                dist = math.hypot(px - x1, py - y1)
            else:
                t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / l2))
                dist = math.hypot(px - (x1 + t * (x2 - x1)), py - (y1 + t * (y2 - y1)))
            if dist < min_dist: min_dist = dist; best_idx = i
        return best_idx

    def draw(self):
        if self.line_id: self.canvas.delete(self.line_id)
        if self.label_id: self.canvas.delete(self.label_id)
        if self.label_bg_id: self.canvas.delete(self.label_bg_id)
        for hid in self.handle_ids: self.canvas.delete(hid)
        self.handle_ids = []
        z = self.wf.zoom
        dash_pattern = (int(5 * z), int(5 * z)) if self.dashed else None
        aw, ah1, ah2 = max(8, int(20 * z)), max(10, int(24 * z)), max(4, int(8 * z))

        self.line_id = self.canvas.create_line(0, 0, 0, 0, arrow=self.arrow_map.get(self.direction, tk.LAST),
                                               arrowshape=(aw, ah1, ah2), width=max(1, int(self.line_width * z)),
                                               fill=self.color, joinstyle=tk.MITER, dash=dash_pattern,
                                               tags=("edge", self.id))

        if self.label:
            self.label_bg_id = self.canvas.create_rectangle(0, 0, 0, 0, fill="#1a1a1a", outline="",
                                                            tags=("edge_label", self.id))
            self.label_id = self.canvas.create_text(0, 0, text=self.label, fill="#ffcc00",
                                                    font=("Helvetica", max(7, int(11 * z)), "bold"),
                                                    tags=("edge_label", self.id))

        self.canvas.tag_lower(self.line_id)
        for i in range(len(self.waypoints)):
            hid = self.canvas.create_oval(0, 0, 0, 0, fill="yellow", outline="#333", width=2,
                                          tags=("waypoint", self.id, str(i)))
            self.handle_ids.append(hid)
        self.update_position()

    def update_position(self):
        z = self.wf.zoom
        coords = []
        mid_px, mid_py = 0, 0

        if not self.waypoints:
            x1, y1 = self.source.get_port_point(self.target.x, self.target.y)
            x4, y4 = self.target.get_port_point(self.source.x, self.source.y)
            if abs(x1 - x4) > abs(y1 - y4):
                mid_x = snap((x1 + x4) / 2)
                coords = [x1 * z, y1 * z, mid_x * z, y1 * z, mid_x * z, y4 * z, x4 * z, y4 * z]
                mid_px, mid_py = mid_x * z, (y1 * z + y4 * z) / 2
            else:
                mid_y = snap((y1 + y4) / 2)
                coords = [x1 * z, y1 * z, x1 * z, mid_y * z, x4 * z, mid_y * z, x4 * z, y4 * z]
                mid_px, mid_py = (x1 * z + x4 * z) / 2, mid_y * z
        else:
            x1, y1 = self.source.get_port_point(self.waypoints[0][0], self.waypoints[0][1])
            x2, y2 = self.target.get_port_point(self.waypoints[-1][0], self.waypoints[-1][1])
            coords.extend([x1 * z, y1 * z])
            for wp in self.waypoints: coords.extend([wp[0] * z, wp[1] * z])
            coords.extend([x2 * z, y2 * z])
            mid_idx = len(self.waypoints) // 2
            mid_px, mid_py = self.waypoints[mid_idx][0] * z, self.waypoints[mid_idx][1] * z

        self.canvas.coords(self.line_id, *coords)
        self.canvas.tag_lower(self.line_id)
        self.canvas.tag_lower("grid")

        if self.label and self.label_id:
            self.canvas.coords(self.label_id, mid_px, mid_py)
            bbox = self.canvas.bbox(self.label_id)
            if bbox:
                bg_col = self.wf.canvas.cget("bg")
                self.canvas.itemconfig(self.label_bg_id, fill=bg_col)
                self.canvas.coords(self.label_bg_id, bbox[0] - 3, bbox[1] - 2, bbox[2] + 3, bbox[3] + 2)
                self.canvas.tag_raise(self.label_bg_id)
                self.canvas.tag_raise(self.label_id)

        st_state = "normal" if self.selected or self.wf.current_mode.get() == "bend" else "hidden"
        fill_c = "#ffcc00" if self.selected else self.color
        self.canvas.itemconfig(self.line_id, fill=fill_c)

        for i, wp in enumerate(self.waypoints):
            hx, hy = wp[0] * z, wp[1] * z;
            r = max(3, int(5 * z))
            self.canvas.coords(self.handle_ids[i], hx - r, hy - r, hx + r, hy + r)
            self.canvas.itemconfig(self.handle_ids[i], state=st_state)
            self.canvas.tag_raise(self.handle_ids[i])

    def set_selected(self, state):
        self.selected = state; self.update_position()

    def update_properties(self, direction, color, dashed, line_width, label=""):
        self.direction = direction;
        self.color = color;
        self.dashed = dashed;
        self.line_width = line_width
        self.label = label;
        self.draw()

    def destroy(self):
        self.canvas.delete(self.line_id)
        if self.label_id: self.canvas.delete(self.label_id)
        if self.label_bg_id: self.canvas.delete(self.label_bg_id)
        for hid in self.handle_ids: self.canvas.delete(hid)

    def to_dict(self):
        return {
            "id": self.id, "source": self.source.id, "target": self.target.id,
            "direction": self.direction, "color": self.color, "dashed": self.dashed,
            "waypoints": self.waypoints, "line_width": getattr(self, "line_width", 2),
            "label": getattr(self, "label", "")
        }


class WorkflowCanvasFrame(ctk.CTkFrame):
    def __init__(self, master, tile_model, close_callback, manager, **kwargs):
        super().__init__(master, **kwargs)
        self.model = tile_model
        self.close_callback = close_callback
        self.manager = manager

        self.nodes = {};
        self.edges = {}
        self.zoom = 1.0
        self.clipboard = {"nodes": [], "edges": []}

        self.history = []
        self.history_idx = -1
        self.has_unsaved_changes = False

        self.resizing_group = False
        self.group_bbox_coords = None
        self.group_start_nodes = []
        self.group_start_bbox = None

        self.dragged_node = None;
        self.resizing_node = None;
        self.dragged_waypoint = None
        self.drawing_state = None;
        self.temp_line = None
        self.pan_start_x = 0;
        self.pan_start_y = 0
        self.lasso_start = None;
        self.lasso_rect = None;
        self.was_dragged = False

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # PASEK GÓRNY
        header = ctk.CTkFrame(self, height=50, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))
        ctk.CTkButton(header, text="< Wróć do listy", width=100, command=self.close_callback).pack(side="left",
                                                                                                   padx=(0, 20))
        ctk.CTkLabel(header, text=f"📍 Workflow: {self.model.title}", font=st.FONT_TITLE).pack(side="left")

        self.coord_lbl = ctk.CTkLabel(header, text="X: 0 | Y: 0", text_color="gray", font=("Helvetica", 12, "bold"))
        self.coord_lbl.pack(side="right", padx=(20, 0))

        if HAS_PIL: ctk.CTkButton(header, text="📸 Eksportuj", width=100, fg_color="#1f538d",
                                  command=self.export_image).pack(side="right", padx=(10, 0))
        self.save_btn = ctk.CTkButton(header, text="💾 Zapisz", width=100, fg_color="green", hover_color="darkgreen",
                                      command=self.save_workflow)
        self.save_btn.pack(side="right", padx=(10, 0))
        ctk.CTkButton(header, text="🗑️ Wyczyść", width=100, fg_color="#8b0000", hover_color="#5c0000",
                      command=self.clear_canvas).pack(side="right")

        # PASEK BOCZNY - PODZIAŁ NA GÓRĘ I DÓŁ, by unikać ucinania!
        self.toolbar = ctk.CTkFrame(self, width=180)
        self.toolbar.grid(row=1, column=0, sticky="ns", padx=(20, 10), pady=(0, 20))

        # Dolna, nieprzewijana sekcja paska narzędzi
        self.toolbar_bottom = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        self.toolbar_bottom.pack(side="bottom", fill="x", pady=5)

        ctk.CTkButton(self.toolbar_bottom, text="🏠 Zresetuj Widok", width=120, command=self.reset_view).pack(
            side="bottom", pady=10)

        zoom_frame = ctk.CTkFrame(self.toolbar_bottom, fg_color="transparent")
        zoom_frame.pack(side="bottom", pady=(5, 10))
        ctk.CTkButton(zoom_frame, text="-", width=30, command=self.zoom_out).pack(side="left", padx=2)
        self.zoom_lbl = ctk.CTkLabel(zoom_frame, text="100%", font=("Helvetica", 12, "bold"), width=45)
        self.zoom_lbl.pack(side="left", padx=2)
        ctk.CTkButton(zoom_frame, text="+", width=30, command=self.zoom_in).pack(side="left", padx=2)

        bg_frame = ctk.CTkFrame(self.toolbar_bottom, fg_color="transparent")
        bg_frame.pack(side="bottom", pady=10)
        ctk.CTkLabel(bg_frame, text="Kolor Tła:", font=("Helvetica", 10)).pack()
        self.canvas_bg_var = ctk.StringVar()
        self.canvas_bg_map = {"Ciemne": "#1a1a1a", "Białe": "#ffffff", "Szare": "#2b2b2b", "Niebieskie": "#1e293b",
                              "Czarne": "#000000"}
        loaded_bg = self.model.workflow_data.get("canvas_bg", "#1a1a1a")
        current_bg_name = "Ciemne"
        for k, v in self.canvas_bg_map.items():
            if v == loaded_bg: current_bg_name = k
        self.canvas_bg_var.set(current_bg_name)
        ctk.CTkOptionMenu(bg_frame, values=list(self.canvas_bg_map.keys()), variable=self.canvas_bg_var,
                          command=self.change_canvas_bg, width=120).pack(pady=2)

        # Górna, przewijana sekcja paska narzędzi (Dla małych monitorów)
        self.toolbar_scroll = ctk.CTkScrollableFrame(self.toolbar, fg_color="transparent", width=170)
        self.toolbar_scroll.pack(side="top", fill="both", expand=True)

        ctk.CTkLabel(self.toolbar_scroll, text="Narzędzia", font=st.FONT_TITLE).pack(pady=(10, 10))

        self.current_mode = tk.StringVar(value="move")
        tools = [("🖱️ Przesuwaj", "move"), ("✋ Przesuń Widok", "pan"), ("🔲 Dodaj Blok", "add_block"),
                 ("↗️ Połącz", "add_edge"), ("🪢 Wyginaj Linie", "bend"), ("❌ Usuń element", "delete")]
        for text, mode in tools:
            rb = ctk.CTkRadioButton(self.toolbar_scroll, text=text, variable=self.current_mode, value=mode,
                                    font=("Helvetica", 13), command=self.on_tool_changed)
            rb.pack(anchor="w", padx=10, pady=8)

        self.context_frame = ctk.CTkFrame(self.toolbar_scroll, fg_color="transparent")
        self.context_frame.pack(fill="x", padx=5, pady=5)

        self.block_options = ctk.CTkFrame(self.context_frame, fg_color="transparent")
        ctk.CTkLabel(self.block_options, text="Typ Bloku:", font=("Helvetica", 11)).pack()
        self.new_node_type = ctk.StringVar(value="block")
        ctk.CTkOptionMenu(self.block_options, values=["block", "note", "project", "text"], variable=self.new_node_type,
                          width=120).pack(pady=2)

        self.edge_options = ctk.CTkFrame(self.context_frame, fg_color="transparent")
        ctk.CTkLabel(self.edge_options, text="Kierunek:", font=("Helvetica", 11)).pack(pady=(0, 2))
        self.dir_keys = {"A ➔ B": "last", "A ⬅ B": "first", "A ⬌ B": "both", "Zwykła linia": "none"}
        self.new_edge_dir = ctk.StringVar(value="A ➔ B")
        ctk.CTkOptionMenu(self.edge_options, values=list(self.dir_keys.keys()), variable=self.new_edge_dir,
                          width=120).pack(pady=2)

        ctk.CTkLabel(self.edge_options, text="Kolor Linii:", font=("Helvetica", 11)).pack(pady=(5, 2))
        self.new_edge_color = ctk.StringVar(value="Szary")
        self.edge_color_map = {"Szary": "#888888", "Czerwony": "#ff4a4a", "Zielony": "#00cc00", "Niebieski": "#2980b9"}
        ctk.CTkOptionMenu(self.edge_options, values=list(self.edge_color_map.keys()), variable=self.new_edge_color,
                          width=120).pack(pady=2)

        ctk.CTkLabel(self.edge_options, text="Grubość:", font=("Helvetica", 11)).pack(pady=(5, 2))
        self.new_edge_width = ctk.StringVar(value="2")
        ctk.CTkOptionMenu(self.edge_options, values=["1", "2", "3", "4", "5"], variable=self.new_edge_width,
                          width=120).pack(pady=2)
        self.new_edge_dashed = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.edge_options, text="Przerywana", variable=self.new_edge_dashed).pack(pady=10)

        # CANVAS I MINIMAPA
        self.canvas_container = ctk.CTkFrame(self)
        self.canvas_container.grid(row=1, column=1, sticky="nsew", padx=(0, 20), pady=(0, 20))

        self.canvas = tk.Canvas(self.canvas_container, bg=loaded_bg, highlightthickness=0,
                                scrollregion=(-10000, -10000, 10000, 10000))
        self.canvas.pack(fill="both", expand=True, padx=2, pady=2)

        self.minimap_size = 200
        self.minimap_scale = 0.01
        self.minimap = tk.Canvas(self.canvas_container, width=self.minimap_size, height=self.minimap_size, bg="#2a2a2a",
                                 highlightthickness=1, highlightbackground="#555")
        self.minimap.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)

        btn_mm_in = tk.Button(self.minimap, text="+", font=("Arial", 8, "bold"), bg="#444", fg="white", relief="flat",
                              bd=0, command=self.minimap_zoom_in)
        btn_mm_in.place(x=5, y=5, width=20, height=20)
        btn_mm_out = tk.Button(self.minimap, text="-", font=("Arial", 8, "bold"), bg="#444", fg="white", relief="flat",
                               bd=0, command=self.minimap_zoom_out)
        btn_mm_out.place(x=5, y=30, width=20, height=20)

        self.minimap.bind("<ButtonPress-1>", self.on_minimap_click)
        self.minimap.bind("<B1-Motion>", self.on_minimap_drag)
        self.minimap.bind("<MouseWheel>", self.on_minimap_wheel)

        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonPress-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.do_pan)
        self.canvas.bind("<ButtonPress-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.do_pan)

        self.canvas.bind("<Delete>", self.on_delete_key)
        self.canvas.bind("<BackSpace>", self.on_delete_key)
        self.canvas.bind("<Control-c>", self.on_copy_key)
        self.canvas.bind("<Control-v>", self.on_paste_key)
        self.canvas.bind("<Control-a>", self.on_select_all)
        self.canvas.bind("<Control-g>", self.on_group_key)
        self.canvas.bind("<Control-u>", self.on_ungroup_key)
        self.canvas.bind("<Control-z>", self.on_undo_key)
        self.canvas.bind("<Control-y>", self.on_redo_key)

        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)

        self.after(50, self.initial_center)
        self.after(100, self.load_workflow)

    def change_canvas_bg(self, choice):
        c = self.canvas_bg_map.get(choice, "#1a1a1a")
        self.canvas.config(bg=c)
        self.mark_unsaved()
        for e in self.edges.values(): e.update_position()

    def minimap_zoom_in(self):
        self.minimap_scale = min(self.minimap_scale * 1.5, 0.05)
        self.update_minimap()

    def minimap_zoom_out(self):
        self.minimap_scale = max(self.minimap_scale / 1.5, 0.002)
        self.update_minimap()

    def on_minimap_wheel(self, event):
        if event.num == 4 or getattr(event, "delta", 0) > 0:
            self.minimap_zoom_in()
        elif event.num == 5 or getattr(event, "delta", 0) < 0:
            self.minimap_zoom_out()

    def to_minimap(self, lx, ly):
        return 100 + (lx * self.minimap_scale), 100 + (ly * self.minimap_scale)

    def update_minimap(self):
        self.minimap.delete("all")

        for e in self.edges.values():
            pts = [self.to_minimap(e.source.x, e.source.y)]
            for wp in e.waypoints: pts.append(self.to_minimap(wp[0], wp[1]))
            pts.append(self.to_minimap(e.target.x, e.target.y))
            flat_pts = []
            for p in pts: flat_pts.extend(p)
            if len(flat_pts) >= 4: self.minimap.create_line(*flat_pts, fill="#888")

        for n in self.nodes.values():
            mx, my = self.to_minimap(n.x, n.y)
            mw, mh = n.width * self.minimap_scale, n.height * self.minimap_scale
            color = n.color if n.color else "#555"
            if n.node_type == "text": color = "#fff"
            self.minimap.create_rectangle(mx - mw / 2, my - mh / 2, mx + mw / 2, my + mh / 2, fill=color, outline="")

        x0 = self.canvas.canvasx(0) / self.zoom
        y0 = self.canvas.canvasy(0) / self.zoom
        x1 = self.canvas.canvasx(self.canvas.winfo_width()) / self.zoom
        y1 = self.canvas.canvasy(self.canvas.winfo_height()) / self.zoom

        vx0, vy0 = self.to_minimap(x0, y0)
        vx1, vy1 = self.to_minimap(x1, y1)
        self.minimap.create_rectangle(vx0, vy0, vx1, vy1, outline="white", width=2, tags="viewport")

    def move_viewport_from_minimap(self, mx, my):
        lx = (mx - 100) / self.minimap_scale
        ly = (my - 100) / self.minimap_scale
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        target_cx = (lx * self.zoom) - cw / 2
        target_cy = (ly * self.zoom) - ch / 2
        frac_x = (target_cx + 10000) / 20000
        frac_y = (target_cy + 10000) / 20000
        self.canvas.xview_moveto(frac_x)
        self.canvas.yview_moveto(frac_y)
        self.draw_grid()
        self.update_minimap()

    def on_minimap_click(self, event):
        self.move_viewport_from_minimap(event.x, event.y)

    def on_minimap_drag(self, event):
        self.move_viewport_from_minimap(event.x, event.y)

    def draw_group_selection(self):
        self.canvas.delete("group_bbox")
        self.canvas.delete("group_handle")
        selected_nodes = [n for n in self.nodes.values() if n.selected]

        if len(selected_nodes) > 1:
            min_x = min(n.x - n.width / 2 for n in selected_nodes)
            min_y = min(n.y - n.height / 2 for n in selected_nodes)
            max_x = max(n.x + n.width / 2 for n in selected_nodes)
            max_y = max(n.y + n.height / 2 for n in selected_nodes)

            z = self.zoom
            self.canvas.create_rectangle(min_x * z, min_y * z, max_x * z, max_y * z, outline="#00ffcc", dash=(4, 4),
                                         width=2, tags="group_bbox")
            hr = 6 * z
            self.canvas.create_rectangle(max_x * z - hr * 2, max_y * z - hr * 2, max_x * z, max_y * z, fill="#00ffcc",
                                         outline="black", tags=("group_handle", "handle"))

            self.group_bbox_coords = (min_x, min_y, max_x, max_y)
            for n in selected_nodes:
                self.canvas.itemconfig(n.handle_id, state="hidden")
        elif len(selected_nodes) == 1:
            self.canvas.itemconfig(selected_nodes[0].handle_id, state="normal")

    def export_image(self):
        ExportDialog(self, self.execute_export)

    def execute_export(self, format_val, show_grid, show_minimap, transparent):
        from customtkinter import filedialog
        ext = ".png" if format_val == "PNG" else ".jpg"
        filepath = filedialog.asksaveasfilename(defaultextension=ext, filetypes=[(f"{format_val} Image", f"*{ext}")])
        if not filepath: return

        for n in self.nodes.values(): n.set_selected(False)
        for e in self.edges.values(): e.set_selected(False)
        self.draw_group_selection()

        if not show_grid: self.canvas.itemconfig("grid", state="hidden")
        if not show_minimap: self.minimap.place_forget()

        old_bg = self.canvas.cget("bg")
        if transparent and format_val == "PNG":
            self.canvas.config(bg="#ff00ff")

        self.update_idletasks()

        x0 = self.canvas.winfo_rootx()
        y0 = self.canvas.winfo_rooty()
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        try:
            img = ImageGrab.grab(bbox=(x0, y0, x0 + w, y0 + h))

            if transparent and format_val == "PNG":
                img = img.convert("RGBA")
                data = img.getdata()
                new_data = []
                for item in data:
                    if item[0] == 255 and item[1] == 0 and item[2] == 255:
                        new_data.append((255, 255, 255, 0))
                    else:
                        new_data.append(item)
                img.putdata(new_data)
            elif format_val == "JPG":
                img = img.convert("RGB")

            img.save(filepath)
            tk.messagebox.showinfo("Eksport", "Zapisano poprawnie!")
        except Exception as e:
            tk.messagebox.showerror("Błąd", f"Nie udało się zapisać: {e}")
        finally:
            self.canvas.config(bg=old_bg)
            self.canvas.itemconfig("grid", state="normal")
            self.minimap.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)

    def mark_unsaved(self):
        if not self.has_unsaved_changes:
            self.has_unsaved_changes = True
            self.save_btn.configure(fg_color="#d47300", hover_color="#a35800", text="💾 Zapisz *")

    def push_to_history(self):
        state = {"nodes": [n.to_dict() for n in self.nodes.values()],
                 "edges": [e.to_dict() for e in self.edges.values()]}
        self.history = self.history[:self.history_idx + 1]
        self.history.append(state)
        self.history_idx += 1
        self.update_minimap()

    def on_undo_key(self, event):
        if self.history_idx > 0:
            self.history_idx -= 1
            self.restore_state(self.history[self.history_idx])

    def on_redo_key(self, event):
        if self.history_idx < len(self.history) - 1:
            self.history_idx += 1
            self.restore_state(self.history[self.history_idx])

    def restore_state(self, state):
        self.canvas.delete("all")
        self.nodes.clear()
        self.edges.clear()
        self.draw_grid()
        self.model.workflow_data = state
        self._render_current_state()
        self.mark_unsaved()
        self.draw_group_selection()
        self.update_minimap()

    def on_mouse_wheel(self, event):
        if event.state & 0x0004:
            if event.num == 4 or getattr(event, "delta", 0) > 0:
                self.zoom_in()
            elif event.num == 5 or getattr(event, "delta", 0) < 0:
                self.zoom_out()

    def on_select_all(self, event):
        for n in self.nodes.values(): n.set_selected(True)
        for e in self.edges.values(): e.set_selected(True)
        self.draw_group_selection()

    def on_group_key(self, event):
        selected_nodes = [n for n in self.nodes.values() if n.selected]
        if len(selected_nodes) > 1:
            new_group_id = str(uuid.uuid4())
            for n in selected_nodes: n.group_id = new_group_id
            self.mark_unsaved()
            self.push_to_history()

    def on_ungroup_key(self, event):
        selected_nodes = [n for n in self.nodes.values() if n.selected]
        if selected_nodes:
            for n in selected_nodes: n.group_id = None
            self.mark_unsaved()
            self.push_to_history()

    def on_delete_key(self, event):
        deleted = False
        nodes_to_delete = [n for n in self.nodes.values() if n.selected]
        for n in nodes_to_delete:
            n.destroy()
            del self.nodes[n.id]
            edges_to_del = [e_id for e_id, e in self.edges.items() if e.source.id == n.id or e.target.id == n.id]
            for e_id in edges_to_del:
                self.edges[e_id].destroy()
                del self.edges[e_id]
            deleted = True

        edges_to_delete = [e for e in self.edges.values() if e.selected]
        for e in edges_to_delete:
            if e.id in self.edges:
                e.destroy()
                del self.edges[e.id]
                deleted = True

        if deleted:
            self.draw_group_selection()
            self.mark_unsaved()
            self.push_to_history()

    def on_copy_key(self, event):
        selected_nodes = [n for n in self.nodes.values() if n.selected]
        selected_node_ids = {n.id for n in selected_nodes}
        selected_edges = [e for e in self.edges.values() if
                          e.source.id in selected_node_ids and e.target.id in selected_node_ids]
        self.clipboard = {"nodes": [n.to_dict() for n in selected_nodes],
                          "edges": [e.to_dict() for e in selected_edges]}

    def on_paste_key(self, event):
        if not getattr(self, "clipboard", None) or not self.clipboard.get("nodes"): return
        for n in self.nodes.values(): n.set_selected(False)
        for e in self.edges.values(): e.set_selected(False)
        id_mapping = {};
        new_nodes = []
        for n_data in self.clipboard["nodes"]:
            old_id = n_data["id"]
            new_id = str(uuid.uuid4())
            px = snap(n_data["x"] + 40);
            py = snap(n_data["y"] + 40)
            node = CanvasNode(
                self, px, py, n_data["text"],
                node_type=n_data["type"], node_id=new_id,
                color=n_data["color"], border_color=n_data.get("border_color"),
                width=n_data["width"], height=n_data["height"], shape=n_data["shape"], header=n_data["header"],
                priority=n_data.get("priority", "medium"), deadline=n_data.get("deadline", ""),
                tags=n_data.get("tags", ""),
                show_days_left=n_data.get("show_days_left", False), group_id=n_data.get("group_id"),
                font_family=n_data.get("font_family", "Helvetica"), font_size=n_data.get("font_size", 12),
                font_color=n_data.get("font_color")
            )
            node.set_selected(True)
            self.nodes[node.id] = node
            new_nodes.append(node)
            id_mapping[old_id] = node

        new_edges = []
        for e_data in self.clipboard.get("edges", []):
            source_node = id_mapping.get(e_data["source"])
            target_node = id_mapping.get(e_data["target"])
            if source_node and target_node:
                new_waypoints = []
                for wp in e_data.get("waypoints", []): new_waypoints.append([snap(wp[0] + 40), snap(wp[1] + 40)])
                edge = CanvasEdge(
                    self, source_node, target_node, direction=e_data.get("direction", "last"),
                    color=e_data.get("color", "#888888"), dashed=e_data.get("dashed", False),
                    waypoints=new_waypoints, line_width=e_data.get("line_width", 2), label=e_data.get("label", "")
                )
                edge.set_selected(True)
                self.edges[edge.id] = edge
                new_edges.append(edge)

        self.clipboard = {"nodes": [n.to_dict() for n in new_nodes], "edges": [e.to_dict() for e in new_edges]}
        self.draw_group_selection()
        self.mark_unsaved()
        self.push_to_history()

    def cancel_drawing(self):
        if getattr(self, "drawing_state", None):
            if self.temp_line:
                self.canvas.delete(self.temp_line)
                self.temp_line = None
            self.drawing_state = None

    def zoom_in(self):
        self.set_zoom(self.zoom * 1.25)

    def zoom_out(self):
        self.set_zoom(self.zoom / 1.25)

    def set_zoom(self, value):
        self.zoom = max(0.2, min(value, 3.0))
        self.zoom_lbl.configure(text=f"{int(self.zoom * 100)}%")
        for n in self.nodes.values(): n.draw()
        for e in self.edges.values(): e.draw()
        self.draw_grid()
        self.draw_group_selection()
        self.update_minimap()

    def initial_center(self):
        self.update_idletasks()  # ZMIANA: Zmusza Tkintera do obliczenia realnych wymiarów ekranu przed rysowaniem siatki
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        frac_x = (10000 - w / 2) / 20000 if w > 0 else 0.48
        frac_y = (10000 - h / 2) / 20000 if h > 0 else 0.48
        self.canvas.xview_moveto(frac_x)
        self.canvas.yview_moveto(frac_y)
        self.update_minimap()
        self.draw_grid()  # ZMIANA: Rysuj siatkę natychmiast po wycentrowaniu!

    def reset_view(self):
        self.set_zoom(1.0)
        self.initial_center()

    def on_canvas_configure(self, event):
        self.draw_grid()
        self.update_minimap()

    def start_pan(self, event):
        if self.current_mode.get() == "add_edge" and getattr(self, "drawing_state", None):
            self.cancel_drawing()
            return
        self.canvas.config(cursor="fleur")
        self.canvas.scan_mark(event.x, event.y)

    def do_pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.draw_grid()
        self.on_tool_changed()
        self.update_minimap()

    def on_mouse_move(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        logical_x = int(cx / self.zoom)
        logical_y = int(cy / self.zoom)
        self.coord_lbl.configure(text=f"X: {logical_x} | Y: {logical_y}")

        if self.current_mode.get() == "add_edge" and getattr(self, "drawing_state", None) and self.temp_line:
            z = self.zoom
            start_node = self.drawing_state["node"]
            items = self.canvas.find_overlapping(cx - 5, cy - 5, cx + 5, cy + 5)
            target_node = None
            for it in items:
                tags = self.canvas.gettags(it)
                if "node" in tags and len(tags) > 1:
                    n = self.nodes.get(tags[1])
                    if n and n != start_node:
                        target_node = n;
                        break

            last_x, last_y = self.drawing_state["waypoints"][-1] if self.drawing_state["waypoints"] else (logical_x,
                                                                                                          logical_y)
            if target_node:
                tx, ty = target_node.get_port_point(last_x, last_y)
            else:
                tx, ty = logical_x, logical_y

            if self.drawing_state["waypoints"]:
                sx, sy = start_node.get_port_point(self.drawing_state["waypoints"][0][0],
                                                   self.drawing_state["waypoints"][0][1])
            else:
                sx, sy = start_node.get_port_point(tx, ty)

            coords = [sx * z, sy * z]
            for wp in self.drawing_state["waypoints"]: coords.extend([wp[0] * z, wp[1] * z])
            coords.extend([tx * z, ty * z])

            self.canvas.coords(self.temp_line, *coords)
            self.canvas.tag_raise(self.temp_line)

    def draw_grid(self, event=None):
        self.canvas.delete("grid")
        step = int(GRID_SIZE * self.zoom)
        if step < 5: return
        x0 = int(self.canvas.canvasx(0));
        y0 = int(self.canvas.canvasy(0))
        x1 = int(self.canvas.canvasx(self.canvas.winfo_width()));
        y1 = int(self.canvas.canvasy(self.canvas.winfo_height()))
        start_x = x0 - (x0 % step);
        start_y = y0 - (y0 % step)

        for i in range(start_x, x1 + step, step): self.canvas.create_line(i, y0, i, y1, fill="#252525", tags="grid")
        for i in range(start_y, y1 + step, step): self.canvas.create_line(x0, i, x1, i, fill="#252525", tags="grid")
        self.canvas.tag_lower("grid")

    def on_tool_changed(self):
        self.cancel_drawing()
        mode = self.current_mode.get()
        self.block_options.pack_forget()
        self.edge_options.pack_forget()

        if mode == "add_edge":
            self.canvas.configure(cursor="crosshair")
            self.edge_options.pack(fill="x")
        elif mode == "delete":
            self.canvas.configure(cursor="pirate")
        elif mode == "add_block":
            self.canvas.configure(cursor="plus")
            self.block_options.pack(fill="x")
        elif mode == "pan":
            self.canvas.configure(cursor="hand2")
        elif mode == "bend":
            self.canvas.configure(cursor="pencil")
        else:
            self.canvas.configure(cursor="arrow")

        for e in self.edges.values(): e.set_selected(e.selected)

    def on_press(self, event):
        self.canvas.focus_set()
        mode = self.current_mode.get()
        if mode == "pan":
            self.start_pan(event)
            return

        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        logical_x = cx / self.zoom
        logical_y = cy / self.zoom

        items = self.canvas.find_overlapping(cx - 5, cy - 5, cx + 5, cy + 5)
        item = self.canvas.find_withtag("current")

        if mode == "add_block":
            dialog = ctk.CTkInputDialog(text="Wpisz nazwę:", title="Nowy element")
            text = dialog.get_input()
            if text:
                ntype = self.new_node_type.get()
                h = 100 if ntype == "project" else 80
                new_node = CanvasNode(self, snap(logical_x), snap(logical_y), text, node_type=ntype, height=h)
                self.nodes[new_node.id] = new_node
                self.mark_unsaved()
                self.push_to_history()

        elif mode == "move":
            clicked_node_id = None;
            clicked_handle_id = None;
            clicked_edge_id = None
            if item:
                tags = self.canvas.gettags(item[0])
                if "group_handle" in tags:
                    self.resizing_group = True
                    selected_nodes = [n for n in self.nodes.values() if n.selected]
                    self.group_start_nodes = [{'node': n, 'x': n.x, 'y': n.y, 'w': n.width, 'h': n.height} for n in
                                              selected_nodes]
                    self.group_start_bbox = self.group_bbox_coords
                    return
                elif "node" in tags and len(tags) > 1:
                    clicked_node_id = tags[1]
                elif "handle" in tags and len(tags) > 1:
                    clicked_handle_id = tags[1]
                elif "waypoint" in tags and len(tags) > 2:
                    edge_id, wp_idx = tags[1], int(tags[2])
                    self.dragged_waypoint = (self.edges.get(edge_id), wp_idx)
                elif "edge" in tags and len(tags) > 1:
                    clicked_edge_id = tags[1]
                elif "edge_label" in tags and len(tags) > 1:
                    clicked_edge_id = tags[1]

            is_ctrl_pressed = (event.state & 0x0004) != 0

            if clicked_handle_id:
                self.resizing_node = self.nodes.get(clicked_handle_id)
                for n in self.nodes.values(): n.set_selected(n.id == self.resizing_node.id)
                self.draw_group_selection()
            elif clicked_node_id:
                node = self.nodes.get(clicked_node_id)
                if is_ctrl_pressed:
                    node.set_selected(not node.selected)
                    self.dragged_node = node if node.selected else None
                else:
                    self.dragged_node = node
                    if not self.dragged_node.selected:
                        if self.dragged_node.group_id:
                            for n in self.nodes.values(): n.set_selected(n.group_id == self.dragged_node.group_id)
                        else:
                            for n in self.nodes.values(): n.set_selected(n.id == clicked_node_id)
                    for e in self.edges.values(): e.set_selected(False)
                self.draw_group_selection()
            elif clicked_edge_id:
                for e in self.edges.values(): e.set_selected(e.id == clicked_edge_id)
                for n in self.nodes.values(): n.set_selected(False)
                self.draw_group_selection()
            elif self.dragged_waypoint:
                pass
            else:
                if not is_ctrl_pressed:
                    for n in self.nodes.values(): n.set_selected(False)
                    for e in self.edges.values(): e.set_selected(False)
                    self.draw_group_selection()
                self.lasso_start = (cx, cy)
                self.lasso_rect = self.canvas.create_rectangle(cx, cy, cx, cy, outline="#4da6ff", dash=(4, 4), width=2)

        elif mode == "bend":
            clicked_waypoint = None;
            clicked_edge = None
            for it in items:
                tags = self.canvas.gettags(it)
                if "waypoint" in tags and len(tags) > 2:
                    clicked_waypoint = (tags[1], int(tags[2])); break
                elif "edge" in tags and len(tags) > 1:
                    clicked_edge = tags[1]

            if clicked_waypoint:
                edge = self.edges.get(clicked_waypoint[0])
                if edge:
                    edge.waypoints.pop(clicked_waypoint[1])
                    edge.draw();
                    self.mark_unsaved()
            elif clicked_edge:
                edge = self.edges.get(clicked_edge)
                if edge:
                    insert_idx = edge.get_closest_segment_index(logical_x, logical_y)
                    edge.waypoints.insert(insert_idx, [snap(logical_x), snap(logical_y)])
                    edge.draw();
                    edge.set_selected(True);
                    self.mark_unsaved()

        elif mode == "add_edge":
            clicked_node = None
            for it in items:
                tags = self.canvas.gettags(it)
                if "node" in tags and len(tags) > 1:
                    clicked_node = self.nodes.get(tags[1]);
                    break

            if getattr(self, "drawing_state", None):
                if clicked_node:
                    if clicked_node != self.drawing_state["node"]:
                        c = self.edge_color_map.get(self.new_edge_color.get(), "#888888")
                        d = self.new_edge_dashed.get()
                        w = int(self.new_edge_width.get())
                        dir_val = self.dir_keys.get(self.new_edge_dir.get(), "last")

                        new_edge = CanvasEdge(
                            self, self.drawing_state["node"], clicked_node,
                            color=c, dashed=d, line_width=w, direction=dir_val,
                            waypoints=self.drawing_state["waypoints"]
                        )
                        self.edges[new_edge.id] = new_edge
                        self.mark_unsaved();
                        self.push_to_history();
                        self.cancel_drawing()
                else:
                    self.drawing_state["waypoints"].append([snap(logical_x), snap(logical_y)])
            else:
                if clicked_node:
                    self.drawing_state = {"node": clicked_node, "waypoints": []}
                    c = self.edge_color_map.get(self.new_edge_color.get(), "#888888")
                    d = (5, 5) if self.new_edge_dashed.get() else ""
                    w = int(self.new_edge_width.get())
                    dir_val = self.dir_keys.get(self.new_edge_dir.get(), "last")
                    arrow_val = {"last": tk.LAST, "first": tk.FIRST, "both": tk.BOTH, "none": tk.NONE}.get(dir_val,
                                                                                                           tk.LAST)
                    self.temp_line = self.canvas.create_line(cx, cy, cx, cy, dash=d, fill=c,
                                                             width=max(1, w * self.zoom), arrow=arrow_val,
                                                             arrowshape=(16, 20, 6))
                    self.canvas.tag_raise(self.temp_line)

    def on_drag(self, event):
        mode = self.current_mode.get()
        if mode == "pan":
            self.do_pan(event)
            return

        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        logical_x = cx / self.zoom
        logical_y = cy / self.zoom

        if mode == "move":
            if getattr(self, "lasso_start", None) and getattr(self, "lasso_rect", None):
                self.canvas.coords(self.lasso_rect, self.lasso_start[0], self.lasso_start[1], cx, cy)
                self.canvas.tag_raise(self.lasso_rect)
                return

            if getattr(self, "resizing_group", False):
                min_x, min_y, old_max_x, old_max_y = self.group_start_bbox
                new_max_x = max(min_x + 50, snap(logical_x))
                new_max_y = max(min_y + 50, snap(logical_y))
                scale_x = (new_max_x - min_x) / (old_max_x - min_x) if old_max_x != min_x else 1
                scale_y = (new_max_y - min_y) / (old_max_y - min_y) if old_max_y != min_y else 1

                for data in self.group_start_nodes:
                    n = data['node']
                    new_nx = min_x + (data['x'] - min_x) * scale_x
                    new_ny = min_y + (data['y'] - min_y) * scale_y
                    new_nw = data['w'] * scale_x
                    new_nh = data['h'] * scale_y
                    n.move_to(new_nx, new_ny);
                    n.resize(new_nw, new_nh)

                for edge in self.edges.values(): edge.update_position()
                self.draw_group_selection()
                self.was_dragged = True

            elif getattr(self, "dragged_waypoint", None):
                edge, wp_idx = self.dragged_waypoint
                edge.waypoints[wp_idx] = [snap(logical_x), snap(logical_y)]
                edge.update_position()
                self.was_dragged = True

            elif self.resizing_node:
                new_w = snap((logical_x - self.resizing_node.x) * 2)
                new_h = snap((logical_y - self.resizing_node.y) * 2)
                self.resizing_node.resize(new_w, new_h)
                for edge in self.edges.values(): edge.update_position()
                self.was_dragged = True

            elif self.dragged_node:
                self.canvas.delete("guide")
                target_x = snap(logical_x)
                target_y = snap(logical_y)
                snap_threshold = 15
                snapped_x = False;
                snapped_y = False

                for n in self.nodes.values():
                    if n == self.dragged_node or n.selected: continue
                    if not snapped_x and abs(n.x - target_x) < snap_threshold:
                        target_x = n.x;
                        snapped_x = True
                        self.canvas.create_line(n.x * self.zoom, -10000, n.x * self.zoom, 10000, fill="#00ffcc",
                                                dash=(4, 4), tags="guide")
                    if not snapped_y and abs(n.y - target_y) < snap_threshold:
                        target_y = n.y;
                        snapped_y = True
                        self.canvas.create_line(-10000, n.y * self.zoom, 10000, n.y * self.zoom, fill="#00ffcc",
                                                dash=(4, 4), tags="guide")

                dx = target_x - self.dragged_node.x
                dy = target_y - self.dragged_node.y

                if dx != 0 or dy != 0:
                    if self.dragged_node.selected:
                        for n in self.nodes.values():
                            if n.selected: n.move_to(n.x + dx, n.y + dy)
                    else:
                        self.dragged_node.move_to(self.dragged_node.x + dx, self.dragged_node.y + dy)

                    for edge in self.edges.values(): edge.update_position()
                    self.draw_group_selection()
                    self.was_dragged = True

    def on_release(self, event):
        self.canvas.delete("guide")

        if getattr(self, "resizing_group", False):
            self.resizing_group = False
            self.mark_unsaved()
            self.push_to_history()

        if getattr(self, "lasso_start", None) and getattr(self, "lasso_rect", None):
            cx = self.canvas.canvasx(event.x)
            cy = self.canvas.canvasy(event.y)
            x1 = min(self.lasso_start[0], cx) / self.zoom
            y1 = min(self.lasso_start[1], cy) / self.zoom
            x2 = max(self.lasso_start[0], cx) / self.zoom
            y2 = max(self.lasso_start[1], cy) / self.zoom

            is_ctrl = (event.state & 0x0004) != 0
            selected_nodes = []
            for n in self.nodes.values():
                if n.x >= x1 and n.x <= x2 and n.y >= y1 and n.y <= y2:
                    selected_nodes.append(n)

            for n in self.nodes.values():
                if is_ctrl and n.selected: continue
                n.set_selected(n in selected_nodes)

            selected_node_ids = [n.id for n in self.nodes.values() if n.selected]
            for e in self.edges.values():
                e.set_selected(e.source.id in selected_node_ids and e.target.id in selected_node_ids)

            self.canvas.delete(self.lasso_rect)
            self.lasso_start = None
            self.lasso_rect = None
            self.draw_group_selection()

        if getattr(self, "was_dragged", False):
            self.mark_unsaved()
            self.push_to_history()
            self.was_dragged = False

        self.dragged_node = None
        self.resizing_node = None
        self.dragged_waypoint = None

    def on_double_click(self, event):
        item = self.canvas.find_withtag("current")
        if not item: return

        tags = self.canvas.gettags(item[0])
        if "node" in tags and len(tags) > 1:
            node = self.nodes.get(tags[1])
            if node: NodeEditDialog(self, node, self.apply_node_edit, self.duplicate_node)
        elif "edge" in tags and len(tags) > 1:
            edge = self.edges.get(tags[1])
            if edge: EdgeEditDialog(self, edge, self.apply_edge_edit)
        elif "edge_label" in tags and len(tags) > 1:
            edge = self.edges.get(tags[1])
            if edge: EdgeEditDialog(self, edge, self.apply_edge_edit)

    def apply_node_edit(self, node, data):
        node.update_properties(data)
        for edge in self.edges.values():
            if edge.source == node or edge.target == node: edge.update_position()
        self.draw_group_selection()
        self.mark_unsaved()
        self.push_to_history()

    def duplicate_node(self, node):
        new_node = CanvasNode(
            self, snap(node.x + 40), snap(node.y + 40), node.text, node.node_type,
            color=node.color, border_color=getattr(node, 'border_color', None), width=node.width, height=node.height,
            shape=node.shape, header=node.header, priority=getattr(node, 'priority', 'medium'),
            deadline=getattr(node, 'deadline', ''), tags=getattr(node, 'tags', ''),
            show_days_left=getattr(node, 'show_days_left', False),
            group_id=getattr(node, 'group_id', None), font_family=node.font_family, font_size=node.font_size,
            font_color=node.font_color
        )
        self.nodes[new_node.id] = new_node
        self.mark_unsaved()
        self.push_to_history()

    def apply_edge_edit(self, edge, new_direction, new_color, new_dashed, line_width, label):
        edge.update_properties(new_direction, new_color, new_dashed, line_width, label)
        self.mark_unsaved()
        self.push_to_history()

    def save_workflow(self):
        self.model.workflow_data["nodes"] = [node.to_dict() for node in self.nodes.values()]
        self.model.workflow_data["edges"] = [edge.to_dict() for edge in self.edges.values()]
        self.model.workflow_data["canvas_bg"] = self.canvas.cget("bg")
        self.manager.save_to_file()
        self.has_unsaved_changes = False
        self.save_btn.configure(fg_color="green", hover_color="darkgreen", text="💾 Zapisz")

    def _render_current_state(self):
        saved_nodes = self.model.workflow_data.get("nodes", [])
        for nd in saved_nodes:
            node = CanvasNode(
                self, x=nd["x"], y=nd["y"], text=nd["text"],
                node_type=nd.get("type", "block"), node_id=nd["id"],
                color=nd.get("color"), border_color=nd.get("border_color"), width=nd.get("width", 160),
                height=nd.get("height", 80),
                shape=nd.get("shape", "rect"), header=nd.get("header", ""),
                priority=nd.get("priority", "medium"), deadline=nd.get("deadline", ""), tags=nd.get("tags", ""),
                show_days_left=nd.get("show_days_left", False), group_id=nd.get("group_id"),
                font_family=nd.get("font_family", "Helvetica"), font_size=nd.get("font_size", 12),
                font_color=nd.get("font_color")
            )
            self.nodes[node.id] = node

        saved_edges = self.model.workflow_data.get("edges", [])
        for ed in saved_edges:
            source_node = self.nodes.get(ed["source"])
            target_node = self.nodes.get(ed["target"])
            if source_node and target_node:
                edge = CanvasEdge(
                    self, source_node, target_node,
                    edge_id=ed["id"], direction=ed.get("direction", "last"),
                    color=ed.get("color", "#888888"), dashed=ed.get("dashed", False),
                    waypoints=ed.get("waypoints", []), line_width=ed.get("line_width", 2), label=ed.get("label", "")
                )
                self.edges[edge.id] = edge

    def load_workflow(self):
        self._render_current_state()
        if not self.history:
            self.push_to_history()

    def clear_canvas(self):
        self.canvas.delete("all")
        self.nodes.clear()
        self.edges.clear()
        self.draw_grid()
        self.mark_unsaved()
        self.push_to_history()


# ==========================================
# (TUTAJ JEST POCZĄTEK TWOJEJ KLASY SmartProjectTilesApp)

# ==========================================
# (TUTAJ JEST POCZĄTEK TWOJEJ KLASY SmartProjectTilesApp)

# ==========================================
# GŁÓWNA APLIKACJA (NIE RUSZAJ)
# ==========================================

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