import customtkinter as ctk
import tkinter as tk
import settings as st
from tkcalendar import DateEntry
from datetime import datetime
from models import ProjectTileModel
from translations import tr, rev_tr


def snap(val): return round(val / 20) * 20


def get_key(d, val, default):
    for k, v in d.items():
        if v == val: return k
    return default


class ExportDialog(ctk.CTkToplevel):
    def __init__(self, master, on_export_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.title(tr("export_title"))
        self.geometry("300x380")
        self.on_export_callback = on_export_callback
        self.transient(master)

        ctk.CTkLabel(self, text=tr("file_format"), font=("Helvetica", 12, "bold")).pack(pady=(15, 5))
        self.format_var = ctk.StringVar(value="PNG")
        # ZMIANA: Dodajemy format EPS!
        ctk.CTkOptionMenu(self, values=["PNG", "JPG", "EPS (Wektor)"], variable=self.format_var).pack(pady=5)

        self.grid_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self, text=tr("show_grid"), variable=self.grid_var).pack(pady=10)

        self.minimap_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self, text=tr("show_minimap"), variable=self.minimap_var).pack(pady=10)

        self.trans_var = ctk.BooleanVar(value=True)
        self.trans_cb = ctk.CTkCheckBox(self, text=tr("transparent_bg"), variable=self.trans_var)
        self.trans_cb.pack(pady=10)
        self.format_var.trace_add("write", self.on_format_change)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text=tr("btn_next"), command=self.do_export, fg_color="green",
                      hover_color="darkgreen").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text=tr("btn_cancel"), command=self.destroy, fg_color="#8b0000",
                      hover_color="#5c0000").pack(side="left", padx=5)

    def on_format_change(self, *args):
        val = self.format_var.get()
        if val == "JPG":
            self.trans_var.set(False)
            self.trans_cb.configure(state="disabled")
            self.grid_var.set(True)
        elif val == "EPS (Wektor)":
            # EPS naturalnie radzi sobie ze świetną jakością, blokujemy zbędne opcje rastrowe
            self.trans_var.set(False)
            self.trans_cb.configure(state="disabled")
            self.grid_var.set(False)
        else:
            self.trans_cb.configure(state="normal")
            self.trans_var.set(True)
            self.grid_var.set(False)

    def do_export(self):
        fmt = self.format_var.get()
        show_grid = self.grid_var.get()
        show_minimap = self.minimap_var.get()
        is_transparent = self.trans_var.get()

        self.destroy()
        self.master.after(250, lambda: self.on_export_callback(fmt, show_grid, show_minimap, is_transparent))


class NodeEditDialog(ctk.CTkToplevel):
    def __init__(self, master, node, on_save_callback, on_duplicate_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.title(tr("node_props"))
        self.geometry("450x650")
        self.node = node
        self.on_save_callback = on_save_callback
        self.on_duplicate_callback = on_duplicate_callback
        self.original_data = self.node.to_dict()
        self.protocol("WM_DELETE_WINDOW", self.cancel_data)
        self.transient(master)
        self.grab_set()

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(side="bottom", fill="x", pady=10, padx=10)
        ctk.CTkButton(self.btn_frame, text=tr("btn_save_simple"), command=self.save_data, fg_color="green",
                      hover_color="darkgreen").pack(side="left", expand=True, padx=5)
        ctk.CTkButton(self.btn_frame, text=tr("btn_cancel"), command=self.cancel_data, fg_color="#8b0000",
                      hover_color="#5c0000").pack(side="left", expand=True, padx=5)
        ctk.CTkButton(self.btn_frame, text=tr("btn_copy"), fg_color="#b8860b", hover_color="#8a6508",
                      command=self.duplicate_data).pack(side="left", expand=True, padx=5)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        f_layer = ctk.CTkFrame(self.scroll)
        f_layer.pack(fill="x", pady=5, ipadx=10, ipady=10)
        ctk.CTkLabel(f_layer, text=tr("layer_manage"), font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 5))
        btn_layer_frame = ctk.CTkFrame(f_layer, fg_color="transparent")
        btn_layer_frame.pack(fill="x")
        ctk.CTkButton(btn_layer_frame, text=tr("bring_front"), command=self.bring_front).pack(side="left", expand=True,
                                                                                              padx=2)
        ctk.CTkButton(btn_layer_frame, text=tr("send_back"), command=self.send_back).pack(side="left", expand=True,
                                                                                          padx=2)

        self.f_type_base = ctk.CTkFrame(self.scroll)
        self.f_type_base.pack(fill="x", pady=5, ipadx=10, ipady=10)
        ctk.CTkLabel(self.f_type_base, text=tr("block_type"), font=("Helvetica", 12, "bold")).pack(anchor="w")
        current_type_key = get_key(st.NODE_TYPES, node.node_type, list(st.NODE_TYPES.keys())[0])
        self.type_var = ctk.StringVar(value=tr(current_type_key))
        self.type_var.trace_add("write", self.on_type_change)
        ctk.CTkOptionMenu(self.f_type_base, values=[tr(k) for k in st.NODE_TYPES.keys()], variable=self.type_var).pack(
            fill="x", pady=5)

        self.f_shape = ctk.CTkFrame(self.scroll, fg_color="transparent")
        ctk.CTkLabel(self.f_shape, text=tr("shape")).pack(anchor="w")
        current_shape_key = get_key(st.NODE_SHAPES, node.shape, list(st.NODE_SHAPES.keys())[0])
        self.shape_var = ctk.StringVar(value=tr(current_shape_key))
        self.shape_var.trace_add("write", self.update_live)
        ctk.CTkOptionMenu(self.f_shape, values=[tr(k) for k in st.NODE_SHAPES.keys()], variable=self.shape_var).pack(
            fill="x", pady=2)

        # --- ZMIANA: PRZEORGANIZOWANA ZAWARTOŚĆ ---
        self.f_text = ctk.CTkFrame(self.scroll)
        self.f_text.pack(fill="x", pady=5, ipadx=10, ipady=10)
        ctk.CTkLabel(self.f_text, text=tr("content"), font=("Helvetica", 12, "bold")).pack(anchor="w")

        ctk.CTkLabel(self.f_text, text=tr("header_empty")).pack(anchor="w", pady=(5, 0))
        self.header_var = ctk.StringVar(value=node.header)
        self.header_var.trace_add("write", self.update_live)
        ctk.CTkEntry(self.f_text, textvariable=self.header_var).pack(fill="x", pady=2)

        ctk.CTkLabel(self.f_text, text=tr("main_text")).pack(anchor="w", pady=(5, 0))
        self.text_box = ctk.CTkTextbox(self.f_text, height=80)
        self.text_box.pack(fill="x", pady=2)
        self.text_box.insert("0.0", node.text)
        self.text_box.bind("<KeyRelease>", self.update_live)

        ctk.CTkLabel(self.f_text, text=tr("tags")).pack(anchor="w", pady=(5, 0))
        self.tags_var = ctk.StringVar(value=getattr(node, "tags", ""))
        self.tags_var.trace_add("write", self.update_live)
        ctk.CTkEntry(self.f_text, textvariable=self.tags_var, placeholder_text=tr("tags_placeholder")).pack(fill="x",
                                                                                                            pady=2)

        self.f_proj = ctk.CTkFrame(self.scroll)
        ctk.CTkLabel(self.f_proj, text=tr("proj_data"), font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(10, 0),
                                                                                             padx=10)
        pr_frame = ctk.CTkFrame(self.f_proj, fg_color="transparent")
        pr_frame.pack(fill="x", pady=2, padx=10)
        ctk.CTkLabel(pr_frame, text=tr("priority")).pack(side="left")

        self.prio_keys = list(st.PRIORITY_RANK.keys())
        prio_label = tr(st.PRIORITY_LABELS.get(getattr(node, "priority", "medium"), "Średni"))
        self.priority_var = ctk.StringVar(value=prio_label)
        ctk.CTkOptionMenu(pr_frame, values=[tr(st.PRIORITY_LABELS[k]) for k in self.prio_keys],
                          variable=self.priority_var, width=120, command=self.update_live).pack(side="right")

        cal_frame = ctk.CTkFrame(self.f_proj, fg_color="transparent")
        cal_frame.pack(fill="x", pady=5, padx=10)
        self.deadline_var = ctk.BooleanVar(value=bool(getattr(node, "deadline", "")))
        self.deadline_cb = ctk.CTkCheckBox(cal_frame, text=tr("set_deadline"), variable=self.deadline_var,
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
        og_drop2 = self.cal.drop_down

        def safe_drop2():
            og_drop2()
            if self.cal._top_cal:
                self.cal._top_cal.lift()
                self.cal._top_cal.attributes('-topmost', True)
        self.cal.drop_down = safe_drop2

        def smart_focus2(event):
            w_type = str(type(event.widget)).lower()
            if "entry" in w_type or "text" in w_type:
                return
            self.focus_set()

        self.bind("<Button-1>", smart_focus2)
        self.show_days_var = ctk.BooleanVar(value=getattr(node, "show_days_left", False))
        ctk.CTkCheckBox(self.f_proj, text=tr("show_days_left"), variable=self.show_days_var,
                        command=self.update_live).pack(anchor="w", pady=(2, 5), padx=15)

        self.f_color = ctk.CTkFrame(self.scroll)
        ctk.CTkLabel(self.f_color, text=tr("colors_header"), font=("Helvetica", 12, "bold")).pack(anchor="w", padx=10,
                                                                                                  pady=(10, 0))

        bg_frame = ctk.CTkFrame(self.f_color, fg_color="transparent")
        bg_frame.pack(fill="x", pady=2, padx=10)
        ctk.CTkLabel(bg_frame, text=tr("bg_color")).pack(side="left")
        current_bg_key = get_key(st.NODE_BG_COLORS, node.color, list(st.NODE_BG_COLORS.keys())[0])
        init_bg_color = st.NODE_BG_COLORS.get(current_bg_key) or "#1e1e1e"
        self.bg_preview = ctk.CTkFrame(bg_frame, width=20, height=20, corner_radius=3, fg_color=init_bg_color)
        self.bg_preview.pack(side="right", padx=(5, 0))
        self.bg_var = ctk.StringVar(value=tr(current_bg_key))
        ctk.CTkOptionMenu(bg_frame, values=[tr(k) for k in st.NODE_BG_COLORS.keys()], variable=self.bg_var, width=130,
                          command=self.update_bg_preview).pack(side="right")

        border_frame = ctk.CTkFrame(self.f_color, fg_color="transparent")
        border_frame.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(border_frame, text=tr("border_color")).pack(side="left")
        current_border_key = get_key(st.NODE_BORDER_COLORS, getattr(node, "border_color", None),
                                     list(st.NODE_BORDER_COLORS.keys())[0])
        init_border_color = st.NODE_BORDER_COLORS.get(current_border_key) or "#666666"
        self.border_preview = ctk.CTkFrame(border_frame, width=20, height=20, corner_radius=3,
                                           fg_color=init_border_color)
        self.border_preview.pack(side="right", padx=(5, 0))
        self.border_var = ctk.StringVar(value=tr(current_border_key))
        ctk.CTkOptionMenu(border_frame, values=[tr(k) for k in st.NODE_BORDER_COLORS.keys()], variable=self.border_var,
                          width=130, command=self.update_border_preview).pack(side="right")

        border_w_frame = ctk.CTkFrame(self.f_color, fg_color="transparent")
        border_w_frame.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(border_w_frame, text=tr("border_thickness")).pack(side="left")
        self.border_width_slider = ctk.CTkSlider(border_w_frame, from_=1, to=8, number_of_steps=7,
                                                 command=self.update_live)
        self.border_width_slider.set(getattr(node, "border_width", 2))
        self.border_width_slider.pack(side="right", padx=(5, 0))

        # --- ZMIANA: ZAKŁADKI TYPOGRAFII (TABVIEW) ---
        self.f_typo = ctk.CTkFrame(self.scroll)
        self.f_typo.pack(fill="x", pady=5, ipadx=5, ipady=5)
        ctk.CTkLabel(self.f_typo, text=tr("typography_tabs"), font=("Helvetica", 12, "bold")).pack(anchor="w", padx=5)

        self.typo_tabs = ctk.CTkTabview(self.f_typo, height=160)
        self.typo_tabs.pack(fill="x", padx=5, pady=5)

        tab_h = self.typo_tabs.add(tr("tab_header"))
        tab_m = self.typo_tabs.add(tr("tab_main"))
        tab_t = self.typo_tabs.add(tr("tab_tags"))
        tab_d = self.typo_tabs.add(tr("tab_date"))

        def build_typo_tab(parent, fam, siz, col, preview_attr_name, update_cb_name):
            fam_var = ctk.StringVar(value=fam)
            siz_var = ctk.StringVar(value=str(siz))
            col_key = get_key(st.CANVAS_FONT_COLORS, col, list(st.CANVAS_FONT_COLORS.keys())[0])
            col_var = ctk.StringVar(value=tr(col_key))

            r1 = ctk.CTkFrame(parent, fg_color="transparent")
            r1.pack(fill="x", pady=2)
            ctk.CTkLabel(r1, text=tr("font")).pack(side="left")
            ctk.CTkOptionMenu(r1, values=st.CANVAS_FONT_FAMILIES, variable=fam_var, width=110,
                              command=self.update_live).pack(side="right")

            r2 = ctk.CTkFrame(parent, fg_color="transparent")
            r2.pack(fill="x", pady=2)
            ctk.CTkLabel(r2, text=tr("font_size")).pack(side="left")
            ctk.CTkOptionMenu(r2, values=st.CANVAS_FONT_SIZES, variable=siz_var, width=110,
                              command=self.update_live).pack(side="right")

            r3 = ctk.CTkFrame(parent, fg_color="transparent")
            r3.pack(fill="x", pady=2)
            ctk.CTkLabel(r3, text=tr("text_color")).pack(side="left")
            init_c = st.CANVAS_FONT_COLORS.get(col_key) or "#ffffff"
            preview = ctk.CTkFrame(r3, width=20, height=20, corner_radius=3, fg_color=init_c)
            preview.pack(side="right", padx=(5, 0))
            setattr(self, preview_attr_name, preview)

            ctk.CTkOptionMenu(r3, values=[tr(k) for k in st.CANVAS_FONT_COLORS.keys()], variable=col_var, width=110,
                              command=getattr(self, update_cb_name)).pack(side="right")
            return fam_var, siz_var, col_var

        self.h_fam, self.h_siz, self.h_col = build_typo_tab(tab_h, getattr(node, "header_font_family", "Helvetica"),
                                                            getattr(node, "header_font_size", 10),
                                                            getattr(node, "header_font_color", None), "h_preview",
                                                            "update_h_preview")
        self.m_fam, self.m_siz, self.m_col = build_typo_tab(tab_m, getattr(node, "font_family", "Helvetica"),
                                                            getattr(node, "font_size", 12),
                                                            getattr(node, "font_color", None), "m_preview",
                                                            "update_m_preview")
        self.t_fam, self.t_siz, self.t_col = build_typo_tab(tab_t, getattr(node, "tags_font_family", "Helvetica"),
                                                            getattr(node, "tags_font_size", 10),
                                                            getattr(node, "tags_font_color", None), "t_preview",
                                                            "update_t_preview")
        self.d_fam, self.d_siz, self.d_col = build_typo_tab(tab_d, getattr(node, "date_font_family", "Helvetica"),
                                                            getattr(node, "date_font_size", 10),
                                                            getattr(node, "date_font_color", None), "d_preview",
                                                            "update_d_preview")

        f_dim = ctk.CTkFrame(self.scroll)
        f_dim.pack(fill="x", pady=5, ipadx=10, ipady=10)
        ctk.CTkLabel(f_dim, text=tr("dimensions_6"), font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 5))
        dim_inner = ctk.CTkFrame(f_dim, fg_color="transparent")
        dim_inner.pack(fill="x")
        ctk.CTkLabel(dim_inner, text=tr("width")).pack(side="left", padx=(0, 5))
        self.width_var = ctk.StringVar(value=str(int(node.width)))
        self.width_var.trace_add("write", self.update_live)
        ctk.CTkEntry(dim_inner, textvariable=self.width_var, width=60, justify="center").pack(side="left", padx=5)

        ctk.CTkLabel(dim_inner, text=tr("height")).pack(side="left", padx=(10, 5))
        self.height_var = ctk.StringVar(value=str(int(node.height)))
        self.height_var.trace_add("write", self.update_live)
        ctk.CTkEntry(dim_inner, textvariable=self.height_var, width=60, justify="center").pack(side="left")
        self.on_type_change()

    def on_type_change(self, *args):
        actual_type = rev_tr(self.type_var.get(), list(st.NODE_TYPES.keys()))
        ntype = st.NODE_TYPES.get(actual_type)
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
        actual_key = rev_tr(choice, list(st.NODE_BG_COLORS.keys()))
        color = st.NODE_BG_COLORS.get(actual_key)
        self.bg_preview.configure(fg_color=color if color else "#1e1e1e")
        self.update_live()

    def update_border_preview(self, choice):
        actual_key = rev_tr(choice, list(st.NODE_BORDER_COLORS.keys()))
        color = st.NODE_BORDER_COLORS.get(actual_key)
        self.border_preview.configure(fg_color=color if color else "#666666")
        self.update_live()

    def update_h_preview(self, choice):
        act = rev_tr(choice, list(st.CANVAS_FONT_COLORS.keys()))
        self.h_preview.configure(fg_color=st.CANVAS_FONT_COLORS.get(act) or "#ffffff")
        self.update_live()

    def update_m_preview(self, choice):
        act = rev_tr(choice, list(st.CANVAS_FONT_COLORS.keys()))
        self.m_preview.configure(fg_color=st.CANVAS_FONT_COLORS.get(act) or "#ffffff")
        self.update_live()

    def update_t_preview(self, choice):
        act = rev_tr(choice, list(st.CANVAS_FONT_COLORS.keys()))
        self.t_preview.configure(fg_color=st.CANVAS_FONT_COLORS.get(act) or "#ffffff")
        self.update_live()

    def update_d_preview(self, choice):
        act = rev_tr(choice, list(st.CANVAS_FONT_COLORS.keys()))
        self.d_preview.configure(fg_color=st.CANVAS_FONT_COLORS.get(act) or "#ffffff")
        self.update_live()

    def _get_internal_priority(self):
        selected_display = self.priority_var.get()
        for k, v in st.PRIORITY_LABELS.items():
            if tr(v) == selected_display: return k
        return "medium"

    def get_current_data(self):
        deadline = self.cal.get_date().strftime("%Y-%m-%d") if self.deadline_var.get() else ""
        act_type = rev_tr(self.type_var.get(), list(st.NODE_TYPES.keys()))
        ntype = st.NODE_TYPES.get(act_type)
        act_shape = rev_tr(self.shape_var.get(), list(st.NODE_SHAPES.keys()))
        shape = "rect" if ntype in ["project", "text"] else st.NODE_SHAPES.get(act_shape)

        try:
            new_w = snap(int(self.width_var.get()))
            new_h = snap(int(self.height_var.get()))
        except ValueError:
            new_w, new_h = self.node.width, self.node.height

        try:
            m_siz = int(self.m_siz.get())
        except ValueError:
            m_siz = 12
        try:
            h_siz = int(self.h_siz.get())
        except ValueError:
            h_siz = 10
        try:
            t_siz = int(self.t_siz.get())
        except ValueError:
            t_siz = 10
        try:
            d_siz = int(self.d_siz.get())
        except ValueError:
            d_siz = 10

        act_bg = rev_tr(self.bg_var.get(), list(st.NODE_BG_COLORS.keys()))
        act_border = rev_tr(self.border_var.get(), list(st.NODE_BORDER_COLORS.keys()))

        act_m_col = rev_tr(self.m_col.get(), list(st.CANVAS_FONT_COLORS.keys()))
        act_h_col = rev_tr(self.h_col.get(), list(st.CANVAS_FONT_COLORS.keys()))
        act_t_col = rev_tr(self.t_col.get(), list(st.CANVAS_FONT_COLORS.keys()))
        act_d_col = rev_tr(self.d_col.get(), list(st.CANVAS_FONT_COLORS.keys()))

        return {
            "text": self.text_box.get("0.0", "end").strip(),
            "header": self.header_var.get(),
            "shape": shape,
            "node_type": ntype,
            "color": st.NODE_BG_COLORS.get(act_bg),
            "border_color": st.NODE_BORDER_COLORS.get(act_border),
            "border_width": int(self.border_width_slider.get()),
            "width": new_w, "height": new_h,
            "priority": self._get_internal_priority(), "deadline": deadline, "tags": self.tags_var.get(),
            "show_days_left": self.show_days_var.get(),

            "font_family": self.m_fam.get(), "font_size": m_siz, "font_color": st.CANVAS_FONT_COLORS.get(act_m_col),
            "header_font_family": self.h_fam.get(), "header_font_size": h_siz,
            "header_font_color": st.CANVAS_FONT_COLORS.get(act_h_col),
            "tags_font_family": self.t_fam.get(), "tags_font_size": t_siz,
            "tags_font_color": st.CANVAS_FONT_COLORS.get(act_t_col),
            "date_font_family": self.d_fam.get(), "date_font_size": d_siz,
            "date_font_color": st.CANVAS_FONT_COLORS.get(act_d_col)
        }

    def update_live(self, *args):
        if not hasattr(self, "width_var"): return
        self.node.update_properties(self.get_current_data())
        for edge in self.master.edges.values():
            if edge.source == self.node or edge.target == self.node:
                edge.update_position()
        self.master.draw_group_selection()
        self.master.mark_unsaved()
        if hasattr(self.master, "update_minimap"): self.master.update_minimap()

    def cancel_data(self):
        self.node.update_properties(self.original_data)
        for edge in self.master.edges.values():
            if edge.source == self.node or edge.target == self.node:
                edge.update_position()
        self.master.draw_group_selection()
        if hasattr(self.master, "update_minimap"): self.master.update_minimap()
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
        self.title(tr("edge_props") if "edge_props" in getattr(st, "translations", {}) else "Właściwości Linii")
        self.geometry("380x600")
        self.edge = edge
        self.on_save_callback = on_save_callback
        self.original_data = self.edge.to_dict()
        self.protocol("WM_DELETE_WINDOW", self.cancel_data)
        self.transient(master)
        self.grab_set()

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(side="bottom", fill="x", pady=10, padx=10)
        ctk.CTkButton(self.btn_frame,
                      text=tr("btn_save_simple") if "btn_save_simple" in getattr(st, "translations", {}) else "Zapisz",
                      command=self.save_data, fg_color="green", hover_color="darkgreen").pack(side="left", expand=True,
                                                                                              padx=5)
        ctk.CTkButton(self.btn_frame,
                      text=tr("btn_cancel") if "btn_cancel" in getattr(st, "translations", {}) else "Anuluj",
                      command=self.cancel_data, fg_color="#8b0000", hover_color="#5c0000").pack(side="left",
                                                                                                expand=True, padx=5)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        # --- SEKCJA 1: TEKST ---
        ctk.CTkLabel(self.scroll, text="Etykieta (Tekst na linii):", font=("Helvetica", 12, "bold")).pack(pady=(5, 2),
                                                                                                          anchor="w",
                                                                                                          padx=10)
        self.label_var = ctk.StringVar(value=getattr(edge, "label", ""))
        self.label_var.trace_add("write", self.update_live)
        ctk.CTkEntry(self.scroll, textvariable=self.label_var, width=300).pack(pady=5, padx=10)

        # --- SEKCJA 2: TYPOGRAFIA ---
        self.f_typo = ctk.CTkFrame(self.scroll)
        self.f_typo.pack(fill="x", pady=10, ipadx=5, ipady=5)
        ctk.CTkLabel(self.f_typo, text="Typografia", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=10,
                                                                                          pady=(5, 0))

        r1 = ctk.CTkFrame(self.f_typo, fg_color="transparent")
        r1.pack(fill="x", pady=2, padx=10)
        ctk.CTkLabel(r1, text="Czcionka:").pack(side="left")
        self.font_fam_var = ctk.StringVar(value=getattr(edge, "font_family", "Helvetica"))
        ctk.CTkOptionMenu(r1, values=st.CANVAS_FONT_FAMILIES, variable=self.font_fam_var, width=130,
                          command=self.update_live).pack(side="right")

        r2 = ctk.CTkFrame(self.f_typo, fg_color="transparent")
        r2.pack(fill="x", pady=2, padx=10)
        ctk.CTkLabel(r2, text="Rozmiar:").pack(side="left")
        self.font_siz_var = ctk.StringVar(value=str(getattr(edge, "font_size", 11)))
        ctk.CTkOptionMenu(r2, values=st.CANVAS_FONT_SIZES, variable=self.font_siz_var, width=130,
                          command=self.update_live).pack(side="right")

        r3 = ctk.CTkFrame(self.f_typo, fg_color="transparent")
        r3.pack(fill="x", pady=2, padx=10)
        ctk.CTkLabel(r3, text="Kolor:").pack(side="left")

        init_font_col = getattr(edge, "font_color", "#ffcc00")
        font_col_key = get_key(st.CANVAS_FONT_COLORS, init_font_col, list(st.CANVAS_FONT_COLORS.keys())[0])
        self.font_col_var = ctk.StringVar(value=tr(font_col_key))
        self.font_col_preview = ctk.CTkFrame(r3, width=20, height=20, corner_radius=3,
                                             fg_color=st.CANVAS_FONT_COLORS.get(font_col_key) or "#ffcc00")
        self.font_col_preview.pack(side="right", padx=(5, 0))
        ctk.CTkOptionMenu(r3, values=[tr(k) for k in st.CANVAS_FONT_COLORS.keys()], variable=self.font_col_var,
                          width=130, command=self.update_font_col_preview).pack(side="right")

        # --- SEKCJA 3: TŁO ETYKIETY ---
        self.f_bg = ctk.CTkFrame(self.scroll)
        self.f_bg.pack(fill="x", pady=5, ipadx=5, ipady=5)
        ctk.CTkLabel(self.f_bg, text="Tło Etykiety", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=10,
                                                                                          pady=(5, 0))

        self.trans_label_var = ctk.BooleanVar(value=getattr(self.edge, "transparent_label", False))
        self.trans_cb = ctk.CTkCheckBox(self.f_bg, text="Przezroczyste (Brak tła)", variable=self.trans_label_var,
                                        command=self.on_trans_change)
        self.trans_cb.pack(pady=(5, 10), padx=10, anchor="w")

        self.r4 = ctk.CTkFrame(self.f_bg, fg_color="transparent")
        self.r4.pack(fill="x", pady=2, padx=10)
        self.bg_lbl = ctk.CTkLabel(self.r4, text="Kolor Tła:")
        self.bg_lbl.pack(side="left")

        init_bg_col = getattr(edge, "label_bg_color", None)
        bg_col_key = get_key(st.NODE_BG_COLORS, init_bg_col,
                             list(st.NODE_BG_COLORS.keys())[0]) if init_bg_col else "Domyślny (Tło Płótna)"

        self.bg_col_var = ctk.StringVar(value=tr(bg_col_key))
        self.bg_col_preview = ctk.CTkFrame(self.r4, width=20, height=20, corner_radius=3,
                                           fg_color=st.NODE_BG_COLORS.get(bg_col_key) or "#1e1e1e")
        self.bg_col_preview.pack(side="right", padx=(5, 0))

        # Specjalna opcja: "Domyślny (Tło Płótna)" aby automatycznie dobierało kolor tła roboczego
        opts = ["Domyślny (Tło Płótna)"] + [tr(k) for k in st.NODE_BG_COLORS.keys()]
        self.bg_col_menu = ctk.CTkOptionMenu(self.r4, values=opts, variable=self.bg_col_var, width=130,
                                             command=self.update_bg_col_preview)
        self.bg_col_menu.pack(side="right")

        # --- SEKCJA 4: STYL LINII ---
        self.f_line = ctk.CTkFrame(self.scroll)
        self.f_line.pack(fill="x", pady=10, ipadx=5, ipady=5)
        ctk.CTkLabel(self.f_line, text="Styl Linii", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=10,
                                                                                          pady=(5, 0))

        l1 = ctk.CTkFrame(self.f_line, fg_color="transparent")
        l1.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(l1, text="Kierunek strzałki:").pack(side="left")
        current_dir_key = get_key(st.EDGE_DIRECTIONS, edge.direction, list(st.EDGE_DIRECTIONS.keys())[0])
        self.dir_var = ctk.StringVar(value=tr(current_dir_key))
        ctk.CTkOptionMenu(l1, values=[tr(k) for k in st.EDGE_DIRECTIONS.keys()], variable=self.dir_var, width=130,
                          command=self.update_live).pack(side="right")

        l2 = ctk.CTkFrame(self.f_line, fg_color="transparent")
        l2.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(l2, text="Kolor linii:").pack(side="left")
        current_ecolor_key = get_key(st.EDGE_COLORS, edge.color, list(st.EDGE_COLORS.keys())[0])
        init_ecolor = st.EDGE_COLORS.get(current_ecolor_key) or "#888888"
        self.edge_color_preview = ctk.CTkFrame(l2, width=20, height=20, corner_radius=3, fg_color=init_ecolor)
        self.edge_color_preview.pack(side="right", padx=(5, 0))
        self.color_var = ctk.StringVar(value=tr(current_ecolor_key))
        ctk.CTkOptionMenu(l2, values=[tr(k) for k in st.EDGE_COLORS.keys()], variable=self.color_var, width=130,
                          command=self.update_edge_color_preview).pack(side="right")

        l3 = ctk.CTkFrame(self.f_line, fg_color="transparent")
        l3.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(l3, text="Grubość:").pack(side="left")
        self.width_slider = ctk.CTkSlider(l3, from_=1, to=8, number_of_steps=7, command=self.update_live)
        self.width_slider.set(edge.line_width)
        self.width_slider.pack(side="right")

        self.dashed_var = ctk.BooleanVar(value=edge.dashed)
        ctk.CTkCheckBox(self.f_line, text="Linia Przerywana", variable=self.dashed_var, command=self.update_live).pack(
            pady=10, anchor="w", padx=10)

        self.on_trans_change()

    def on_trans_change(self, *args):
        if self.trans_label_var.get():
            self.bg_col_menu.configure(state="disabled")
            self.bg_lbl.configure(text_color="gray")
        else:
            self.bg_col_menu.configure(state="normal")
            self.bg_lbl.configure(text_color=["#000000", "#FFFFFF"])
        self.update_live()

    def update_font_col_preview(self, choice):
        act = rev_tr(choice, list(st.CANVAS_FONT_COLORS.keys()))
        self.font_col_preview.configure(fg_color=st.CANVAS_FONT_COLORS.get(act) or "#ffffff")
        self.update_live()

    def update_bg_col_preview(self, choice):
        if choice == "Domyślny (Tło Płótna)":
            self.bg_col_preview.configure(fg_color=self.master.canvas.cget("bg"))
        else:
            act = rev_tr(choice, list(st.NODE_BG_COLORS.keys()))
            self.bg_col_preview.configure(fg_color=st.NODE_BG_COLORS.get(act) or "#1e1e1e")
        self.update_live()

    def update_edge_color_preview(self, choice):
        actual_key = rev_tr(choice, list(st.EDGE_COLORS.keys()))
        color = st.EDGE_COLORS.get(actual_key)
        self.edge_color_preview.configure(fg_color=color if color else "#888888")
        self.update_live()

    def get_current_data(self):
        act_dir = rev_tr(self.dir_var.get(), list(st.EDGE_DIRECTIONS.keys()))
        act_col = rev_tr(self.color_var.get(), list(st.EDGE_COLORS.keys()))

        new_dir = st.EDGE_DIRECTIONS.get(act_dir)
        new_color = st.EDGE_COLORS.get(act_col)
        new_dashed = self.dashed_var.get()
        new_w = int(self.width_slider.get())
        new_label = self.label_var.get()
        is_trans_label = self.trans_label_var.get()

        act_font_col = rev_tr(self.font_col_var.get(), list(st.CANVAS_FONT_COLORS.keys()))
        font_col = st.CANVAS_FONT_COLORS.get(act_font_col)

        if self.bg_col_var.get() == "Domyślny (Tło Płótna)":
            bg_col = None
        else:
            act_bg_col = rev_tr(self.bg_col_var.get(), list(st.NODE_BG_COLORS.keys()))
            bg_col = st.NODE_BG_COLORS.get(act_bg_col)

        try:
            f_size = int(self.font_siz_var.get())
        except ValueError:
            f_size = 11

        return (new_dir, new_color, new_dashed, new_w, new_label, is_trans_label,
                bg_col, self.font_fam_var.get(), f_size, font_col)

    def update_live(self, *args):
        if not hasattr(self, "width_slider"): return
        data = self.get_current_data()
        self.edge.update_properties(*data)
        self.master.mark_unsaved()
        if hasattr(self.master, "update_minimap"): self.master.update_minimap()

    def cancel_data(self):
        orig = self.original_data
        self.edge.update_properties(
            orig["direction"], orig["color"], orig["dashed"], orig.get("line_width", 2),
            orig.get("label", ""), orig.get("transparent_label", False),
            orig.get("label_bg_color", None), orig.get("font_family", "Helvetica"),
            orig.get("font_size", 11), orig.get("font_color", "#ffcc00")
        )
        if hasattr(self.master, "update_minimap"): self.master.update_minimap()
        self.destroy()
    def save_data(self):
        data = self.get_current_data()
        self.on_save_callback(self.edge, *data)
        self.destroy()

class TileFormDialog(ctk.CTkToplevel):
    def __init__(self, master, on_save_callback, existing_tile=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_save_callback = on_save_callback
        self.existing_tile = existing_tile

        self.title(tr("edit_tile") if self.existing_tile else tr("add_new_tile"))
        self.geometry("650x700")
        self.transient(master)
        self.grab_set()
        self.build_form()

    def _get_internal_priority(self):
        selected_display = self.priority_var.get()
        for k, v in st.PRIORITY_LABELS.items():
            if tr(v) == selected_display: return k
        return "medium"

    def build_form(self):
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text=tr("title")).grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.title_entry = ctk.CTkEntry(self)
        self.title_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self, text=tr("priority")).grid(row=1, column=0, padx=10, pady=10, sticky="e")

        self.prio_keys = list(st.PRIORITY_RANK.keys())
        self.priority_var = ctk.StringVar(value=tr(st.PRIORITY_LABELS["medium"]))
        self.priority_menu = ctk.CTkOptionMenu(self, values=[tr(st.PRIORITY_LABELS[k]) for k in self.prio_keys],
                                               variable=self.priority_var)
        self.priority_menu.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.deadline_var = ctk.BooleanVar(value=False)
        self.deadline_cb = ctk.CTkCheckBox(self, text=tr("set_deadline"), variable=self.deadline_var,
                                           command=self.toggle_deadline)
        self.deadline_cb.grid(row=2, column=0, padx=10, pady=10, sticky="e")

        self.cal = DateEntry(self, width=12, background='darkblue', foreground='white', borderwidth=2,
                             date_pattern='y-mm-dd', state="disabled")
        self.cal.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        # --- SMART FIX DLA KALENDARZA I PÓL TEKSTOWYCH ---
        og_drop = self.cal.drop_down

        def safe_drop():
            og_drop()
            if self.cal._top_cal:
                self.cal._top_cal.lift()
                self.cal._top_cal.attributes('-topmost', True)

        self.cal.drop_down = safe_drop

        def smart_focus(event):
            # Jeśli kliknięto w pole tekstowe (Entry/Text), nie zabieraj ostrości!
            w_type = str(type(event.widget)).lower()
            if "entry" in w_type or "text" in w_type:
                return
            self.focus_set()

        self.bind("<Button-1>", smart_focus)
        # -------------------------------------------------
        self.workflow_var = ctk.BooleanVar(value=False)
        self.workflow_cb = ctk.CTkCheckBox(self, text=tr("enable_wf"), variable=self.workflow_var)
        self.workflow_cb.grid(row=3, column=0, columnspan=2, padx=10, pady=5)

        ctk.CTkLabel(self, text=tr("tags")).grid(row=4, column=0, padx=10, pady=10, sticky="e")
        self.tags_entry = ctk.CTkEntry(self, placeholder_text=tr("tags_placeholder"))
        self.tags_entry.grid(row=4, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self, text=tr("desc")).grid(row=5, column=0, padx=10, pady=10, sticky="ne")
        self.text_box = ctk.CTkTextbox(self, height=80)
        self.text_box.grid(row=5, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self, text=tr("tasks")).grid(row=6, column=0, padx=10, pady=10, sticky="ne")
        self.todos_box = ctk.CTkTextbox(self, height=100)
        self.todos_box.grid(row=6, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self, text=tr("bg_color_label")).grid(row=7, column=0, padx=10, pady=10, sticky="e")
        color_frame = ctk.CTkFrame(self, fg_color="transparent")
        color_frame.grid(row=7, column=1, padx=10, pady=10, sticky="ew")
        color_frame.grid_columnconfigure(0, weight=1)

        self.color_var = ctk.StringVar(value=tr("Domyślny"))
        self.color_menu = ctk.CTkOptionMenu(color_frame, values=[tr(k) for k in st.CUSTOM_TILE_COLORS.keys()],
                                            variable=self.color_var, command=self.update_color_preview)
        self.color_menu.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.color_preview = ctk.CTkFrame(color_frame, width=30, height=30, corner_radius=5, border_width=1,
                                          border_color="gray")
        self.color_preview.grid(row=0, column=1)
        self.update_color_preview(tr("Domyślny"))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=8, column=0, columnspan=2, pady=20)
        ctk.CTkButton(btn_frame, text=tr("btn_save_simple"), command=self.save_data).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text=tr("btn_cancel"), command=self.destroy, fg_color="gray").pack(side="left",
                                                                                                    padx=10)

        if self.existing_tile:
            self.title_entry.insert(0, self.existing_tile.title)
            self.priority_var.set(tr(st.PRIORITY_LABELS.get(self.existing_tile.priority, "Średni")))

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
                        self.color_var.set(tr(name))
                        self.update_color_preview(tr(name))
                        break

    def update_color_preview(self, selected_color_display):
        actual_key = rev_tr(selected_color_display, list(st.CUSTOM_TILE_COLORS.keys()))
        color_val = st.CUSTOM_TILE_COLORS.get(actual_key)
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

        act_col_key = rev_tr(self.color_var.get(), list(st.CUSTOM_TILE_COLORS.keys()))
        selected_color = st.CUSTOM_TILE_COLORS.get(act_col_key)

        content = {"text": desc_text if desc_text else None, "todos": todos_list}

        if self.existing_tile:
            self.existing_tile.title = title
            self.existing_tile.priority = self._get_internal_priority()
            self.existing_tile.deadline = deadline
            self.existing_tile.tags = tags
            self.existing_tile.content = content
            self.existing_tile.color = selected_color
            self.existing_tile.has_workflow = has_workflow
            self.on_save_callback(self.existing_tile)
        else:
            new_tile = ProjectTileModel(
                title=title, tags=tags, priority=self._get_internal_priority(),
                deadline=deadline, content=content, color=selected_color, has_workflow=has_workflow
            )
            self.on_save_callback(new_tile)

        self.destroy()


class HelpDialog(ctk.CTkToplevel):
    def __init__(self, master, context="main", **kwargs):
        super().__init__(master, **kwargs)
        self.title(tr("help_title"))
        self.geometry("500x600")
        self.transient(master)
        self.grab_set()

        lbl_title = ctk.CTkLabel(self, text=tr("help_title"), font=("Helvetica", 18, "bold"))
        lbl_title.pack(pady=(15, 10))

        textbox = ctk.CTkTextbox(self, wrap="word", font=("Helvetica", 13))
        textbox.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        if context == "main":
            text = tr("help_main")
        elif context == "calendar":
            text = tr("help_calendar")
        elif context == "workflow":
            text = tr("help_workflow")
        elif context == "statistics":
            text = tr("help_statistics")
        else:
            text = tr("no_help")

        textbox.insert("0.0", text)
        textbox.configure(state="disabled")

        # ZMIANA: Dyskretny podpis twórcy ikony pod polem tekstowym
        credits_text = "Application icon created by Those Icons, and downloaded from ICON-ICONS"
        ctk.CTkLabel(self, text=credits_text, font=("Helvetica", 10), text_color="gray").pack(pady=(0, 5))

        ctk.CTkButton(self, text=tr("btn_understand"), command=self.destroy, fg_color="#1f538d").pack(pady=(5, 15))