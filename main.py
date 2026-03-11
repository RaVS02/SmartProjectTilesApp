import customtkinter as ctk
import settings as st
from models import TileManager, ProjectTileModel
from ui import ProjectTileWidget, TileFormDialog
import math
import tkinter as tk
import uuid

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("green")

# --- ZMIENNE GLOBALNE ---
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
# OKIENKA EDYCJI (WŁAŚCIWOŚCI)
# ==========================================
class NodeEditDialog(ctk.CTkToplevel):
    def __init__(self, master, node, on_save_callback, on_duplicate_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Właściwości Elementu")
        self.geometry("400x650")
        self.node = node
        self.on_save_callback = on_save_callback
        self.on_duplicate_callback = on_duplicate_callback

        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(self, text="Nagłówek (np. Typ):").pack(pady=(15, 0))
        self.header_var = ctk.StringVar(value=node.header)
        ctk.CTkEntry(self, textvariable=self.header_var, width=280).pack(pady=5)

        ctk.CTkLabel(self, text="Tekst główny (obsługuje wiele linii):").pack(pady=(10, 0))
        self.text_box = ctk.CTkTextbox(self, width=280, height=80)
        self.text_box.pack(pady=5)
        self.text_box.insert("0.0", node.text)

        ctk.CTkLabel(self, text="Kształt bloku:").pack(pady=(10, 0))
        self.shapes = {
            "Prostokąt zaokrąglony": "rect",
            "Romb (Decyzja)": "diamond",
            "Elipsa (Start/Koniec)": "oval",
            "Równoległobok (We/Wy)": "parallelogram"
        }
        current_shape = "Prostokąt zaokrąglony"
        for k, v in self.shapes.items():
            if v == node.shape: current_shape = k
        self.shape_var = ctk.StringVar(value=current_shape)
        ctk.CTkOptionMenu(self, values=list(self.shapes.keys()), variable=self.shape_var).pack(pady=5)

        ctk.CTkLabel(self, text="Kolor kafelka:").pack(pady=(10, 0))
        self.colors = {
            "Domyślny Ciemny": None, "Czerwony (Krytyczny)": "#8b0000",
            "Zielony (Sukces)": "#1b4d30", "Pomarańczowy (Uwaga)": "#b35900",
            "Fioletowy (Zewnętrzny)": "#3c1361", "Żółty (Komentarz)": "#b38f00", "Biały": "#ffffff"
        }
        current_color = "Domyślny Ciemny"
        for k, v in self.colors.items():
            if v == node.color: current_color = k
        self.color_var = ctk.StringVar(value=current_color)
        ctk.CTkOptionMenu(self, values=list(self.colors.keys()), variable=self.color_var).pack(pady=5)

        dim_frame = ctk.CTkFrame(self, fg_color="transparent")
        dim_frame.pack(pady=10)
        ctk.CTkLabel(dim_frame, text="Szerokość:").grid(row=0, column=0, padx=5)
        self.width_var = ctk.StringVar(value=str(int(node.width)))
        ctk.CTkEntry(dim_frame, textvariable=self.width_var, width=60, justify="center").grid(row=0, column=1, padx=5)
        ctk.CTkLabel(dim_frame, text="Wysokość:").grid(row=0, column=2, padx=5)
        self.height_var = ctk.StringVar(value=str(int(node.height)))
        ctk.CTkEntry(dim_frame, textvariable=self.height_var, width=60, justify="center").grid(row=0, column=3, padx=5)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="Zapisz", command=self.save_data, width=100).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="📑 Kopiuj", fg_color="#b8860b", hover_color="#8a6508",
                      command=self.duplicate_data, width=100).pack(side="left", padx=5)

    def save_data(self):
        new_text = self.text_box.get("0.0", "end").strip()
        new_header = self.header_var.get()
        new_shape = self.shapes.get(self.shape_var.get())
        new_color = self.colors.get(self.color_var.get())
        try:
            new_w = snap(int(self.width_var.get()))
            new_h = snap(int(self.height_var.get()))
        except ValueError:
            new_w, new_h = self.node.width, self.node.height

        self.on_save_callback(self.node, new_text, new_header, new_shape, new_color, new_w, new_h)
        self.destroy()

    def duplicate_data(self):
        self.on_duplicate_callback(self.node)
        self.destroy()


class EdgeEditDialog(ctk.CTkToplevel):
    def __init__(self, master, edge, on_save_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Właściwości Linii")
        self.geometry("300x350")
        self.edge = edge
        self.on_save_callback = on_save_callback

        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(self, text="Typ strzałki:").pack(pady=(15, 5))
        self.directions = {
            "A ➔ B (Domyślny)": "last", "A ⬅ B (Odwrotny)": "first",
            "A ⬌ B (Dwukierunkowy)": "both", "Linia zwykła (Brak)": "none"
        }
        current_dir = "A ➔ B (Domyślny)"
        for k, v in self.directions.items():
            if v == edge.direction: current_dir = k
        self.dir_var = ctk.StringVar(value=current_dir)
        ctk.CTkOptionMenu(self, values=list(self.directions.keys()), variable=self.dir_var).pack(pady=5)

        ctk.CTkLabel(self, text="Kolor Linii:").pack(pady=(15, 5))
        self.edge_colors = {
            "Szary (Domyślny)": "#888888", "Czerwony (Błąd/Nie)": "#ff4a4a",
            "Zielony (Sukces/Tak)": "#00cc00", "Niebieski (Informacja)": "#2980b9"
        }
        current_ecolor = "Szary (Domyślny)"
        for k, v in self.edge_colors.items():
            if v == edge.color: current_ecolor = k
        self.color_var = ctk.StringVar(value=current_ecolor)
        ctk.CTkOptionMenu(self, values=list(self.edge_colors.keys()), variable=self.color_var).pack(pady=5)

        self.dashed_var = ctk.BooleanVar(value=edge.dashed)
        ctk.CTkCheckBox(self, text="Linia Przerywana", variable=self.dashed_var).pack(pady=15)

        ctk.CTkButton(self, text="Zapisz", command=self.save_data).pack(pady=20)

    def save_data(self):
        new_dir = self.directions.get(self.dir_var.get())
        new_color = self.edge_colors.get(self.color_var.get())
        new_dashed = self.dashed_var.get()
        self.on_save_callback(self.edge, new_dir, new_color, new_dashed)
        self.destroy()


# ==========================================
# KLASY PŁÓTNA (CANVAS)
# ==========================================
class CanvasNode:
    def __init__(self, wf, x, y, text, node_type="block", node_id=None, color=None, width=160, height=80, shape="rect",
                 header=""):
        self.wf = wf
        self.canvas = wf.canvas
        self.id = node_id if node_id else str(uuid.uuid4())

        self.width = snap(width)
        self.height = snap(height)
        self.x = snap(x)
        self.y = snap(y)

        self.text = text
        self.header = header
        self.shape = shape
        self.node_type = node_type
        self.color = color
        self.selected = False

        self.bg_id = None
        self.text_id = None
        self.header_id = None
        self.handle_id = None
        self.draw()

    def draw(self):
        if self.bg_id: self.canvas.delete(self.bg_id)
        if self.text_id: self.canvas.delete(self.text_id)
        if self.header_id: self.canvas.delete(self.header_id)
        if self.handle_id: self.canvas.delete(self.handle_id)

        z = self.wf.zoom
        sx, sy = self.x * z, self.y * z
        sw, sh = self.width * z, self.height * z

        x1, y1 = sx - sw / 2, sy - sh / 2
        x2, y2 = sx + sw / 2, sy + sh / 2

        if self.shape == "oval":
            self.bg_id = self.canvas.create_oval(x1, y1, x2, y2, width=max(1, int(2 * z)), tags=("node", self.id))
        elif self.shape == "diamond":
            pts = [sx, y1, x2, sy, sx, y2, x1, sy]
            self.bg_id = self.canvas.create_polygon(pts, width=max(1, int(2 * z)), tags=("node", self.id))
        elif self.shape == "parallelogram":
            offset = sw * 0.15
            pts = [x1 + offset, y1, x2, y1, x2 - offset, y2, x1, y2]
            self.bg_id = self.canvas.create_polygon(pts, width=max(1, int(2 * z)), tags=("node", self.id))
        else:
            pts = get_round_rect_points(x1, y1, x2, y2, r=12 * z)
            self.bg_id = self.canvas.create_polygon(pts, smooth=True, width=max(1, int(2 * z)), tags=("node", self.id))

        text_color = "black" if self.color == "#ffffff" else "#DCE4EE"
        header_color = "gray" if self.color == "#ffffff" else "#999999"

        font_size = max(6, int(11 * z))
        header_font_size = max(5, int(9 * z))

        self.header_id = self.canvas.create_text(
            sx, sy - sh / 2 + 10 * z, text=self.header, fill=header_color, font=("Helvetica", header_font_size),
            width=sw - 20 * z, justify="center", tags=("node", self.id)
        )
        self.text_id = self.canvas.create_text(
            sx, sy + (10 * z if self.header else 0), text=self.text, fill=text_color,
            font=("Helvetica", font_size, "bold"),
            width=sw - 20 * z, justify="center", tags=("node", self.id)
        )

        self.handle_id = self.canvas.create_rectangle(
            x2 - 12 * z, y2 - 12 * z, x2, y2, fill="white", outline="#333", tags=("handle", self.id), state="hidden"
        )

        self.update_visuals()

    def move_to(self, x, y):
        self.x = x
        self.y = y
        self.draw()

    def resize(self, w, h):
        self.width = max(80, w)
        self.height = max(50, h)
        self.draw()

    def set_selected(self, state):
        self.selected = state
        if self.handle_id:
            self.canvas.itemconfig(self.handle_id, state="normal" if state else "hidden")
        self.update_visuals()

    def update_visuals(self):
        bg = self.color if self.color else ("#b35900" if self.node_type == "note" else "#2b2b2b")
        outline = "#ffcc00" if self.selected else ("#e67300" if self.node_type == "note" else "#666666")
        if self.bg_id:
            self.canvas.itemconfig(self.bg_id, fill=bg, outline=outline)

    def update_properties(self, text, header, shape, color, width, height):
        self.text = text
        self.header = header
        self.shape = shape
        self.color = color
        self.width = width
        self.height = height
        self.draw()

    def destroy(self):
        self.canvas.delete(self.bg_id)
        self.canvas.delete(self.text_id)
        self.canvas.delete(self.header_id)
        self.canvas.delete(self.handle_id)

    def to_dict(self):
        return {
            "id": self.id, "x": self.x, "y": self.y, "text": self.text, "header": self.header,
            "type": self.node_type, "shape": self.shape, "color": self.color, "width": self.width, "height": self.height
        }


# --- ZMIANA: Klasa Edge z obsługą zginania linii (Waypoints) ---
class CanvasEdge:
    def __init__(self, wf, source_node, target_node, edge_id=None, direction="last", color="#888888", dashed=False,
                 waypoints=None):
        self.wf = wf
        self.canvas = wf.canvas
        self.id = edge_id if edge_id else str(uuid.uuid4())
        self.source = source_node
        self.target = target_node
        self.direction = direction
        self.color = color
        self.dashed = dashed

        # Punkty łamania linii trzymane jako lista list: [[x, y], [x, y]]
        self.waypoints = waypoints if waypoints else []

        self.arrow_map = {"last": tk.LAST, "first": tk.FIRST, "both": tk.BOTH, "none": tk.NONE}
        self.line_id = None
        self.handle_ids = []  # Kółeczka na zakrętach
        self.draw()

    def get_edge_point(self, node, target_x, target_y):
        dx = target_x - node.x
        dy = target_y - node.y
        if dx == 0 and dy == 0: return node.x, node.y

        hw, hh = node.width / 2 + 4, node.height / 2 + 4
        if node.shape == "diamond":
            hw -= 10
            hh -= 10

        if dx == 0: return node.x, node.y + (hh if dy > 0 else -hh)
        if dy == 0: return node.x + (hw if dx > 0 else -hw), node.y

        slope = dy / dx
        x_edge = hw if dx > 0 else -hw
        y_edge = x_edge * slope

        if abs(y_edge) <= hh:
            return node.x + x_edge, node.y + y_edge

        y_edge = hh if dy > 0 else -hh
        x_edge = y_edge / slope
        return node.x + x_edge, node.y + y_edge

    def get_closest_segment_index(self, px, py):
        """Matematyka do znajdowania miejsca, w którym kliknęliśmy linię (aby dodać nowy zakręt)"""
        if not self.waypoints: return 0

        pts = [[self.source.x, self.source.y]] + self.waypoints + [[self.target.x, self.target.y]]
        min_dist = float('inf')
        best_idx = 0
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            l2 = (x2 - x1) ** 2 + (y2 - y1) ** 2
            if l2 == 0:
                dist = math.hypot(px - x1, py - y1)
            else:
                t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / l2))
                proj_x = x1 + t * (x2 - x1)
                proj_y = y1 + t * (y2 - y1)
                dist = math.hypot(px - proj_x, py - proj_y)
            if dist < min_dist:
                min_dist = dist
                best_idx = i
        return best_idx

    def draw(self):
        if self.line_id: self.canvas.delete(self.line_id)
        for hid in self.handle_ids: self.canvas.delete(hid)
        self.handle_ids = []

        z = self.wf.zoom
        dash_pattern = (int(5 * z), int(5 * z)) if self.dashed else None
        aw, ah1, ah2 = max(8, int(20 * z)), max(10, int(24 * z)), max(4, int(8 * z))

        # Tworzymy "pustą" linię, która zaraz otrzyma precyzyjne koordynaty
        self.line_id = self.canvas.create_line(
            0, 0, 0, 0,
            arrow=self.arrow_map.get(self.direction, tk.LAST),
            arrowshape=(aw, ah1, ah2), width=max(1, int(3 * z)), fill=self.color,
            joinstyle=tk.MITER, dash=dash_pattern, tags=("edge", self.id)
        )
        self.canvas.tag_lower(self.line_id)

        # Tworzymy uchwyty dla punktów kontrolnych
        for i in range(len(self.waypoints)):
            hid = self.canvas.create_oval(0, 0, 0, 0, fill="yellow", outline="#333", width=2,
                                          tags=("waypoint", self.id, str(i)))
            self.handle_ids.append(hid)

        self.update_position()

    def update_position(self):
        z = self.wf.zoom
        coords = []

        if not self.waypoints:
            # Domyślne łączenie (kształt Z)
            x1, y1 = self.get_edge_point(self.source, self.target.x, self.target.y)
            x4, y4 = self.get_edge_point(self.target, self.source.x, self.source.y)
            mid_x = snap((x1 + x4) / 2)
            coords = [x1 * z, y1 * z, mid_x * z, y1 * z, mid_x * z, y4 * z, x4 * z, y4 * z]
        else:
            # Połączenie po zdefiniowanych przez użytkownika punktach (Waypoints)
            x1, y1 = self.get_edge_point(self.source, self.waypoints[0][0], self.waypoints[0][1])
            x2, y2 = self.get_edge_point(self.target, self.waypoints[-1][0], self.waypoints[-1][1])

            coords.extend([x1 * z, y1 * z])
            for wp in self.waypoints:
                coords.extend([wp[0] * z, wp[1] * z])
            coords.extend([x2 * z, y2 * z])

        self.canvas.coords(self.line_id, *coords)
        self.canvas.tag_lower(self.line_id)
        self.canvas.tag_raise(self.line_id, "grid")

        # Aktualizacja żółtych uchwytów
        for i, wp in enumerate(self.waypoints):
            hx, hy = wp[0] * z, wp[1] * z
            r = max(3, int(5 * z))
            self.canvas.coords(self.handle_ids[i], hx - r, hy - r, hx + r, hy + r)
            self.canvas.tag_raise(self.handle_ids[i])

    def update_properties(self, direction, color, dashed):
        self.direction = direction
        self.color = color
        self.dashed = dashed
        self.draw()

    def destroy(self):
        self.canvas.delete(self.line_id)
        for hid in self.handle_ids: self.canvas.delete(hid)

    def to_dict(self):
        return {
            "id": self.id, "source": self.source.id, "target": self.target.id,
            "direction": self.direction, "color": self.color, "dashed": self.dashed,
            "waypoints": self.waypoints
        }


class WorkflowCanvasFrame(ctk.CTkFrame):
    def __init__(self, master, tile_model, close_callback, manager, **kwargs):
        super().__init__(master, **kwargs)
        self.model = tile_model
        self.close_callback = close_callback
        self.manager = manager

        self.nodes = {}
        self.edges = {}
        self.zoom = 1.0

        self.dragged_node = None
        self.resizing_node = None
        self.edge_start_node = None
        self.temp_line = None
        self.dragged_waypoint = None  # NOWE: Do przesuwania zakrętów

        self.pan_start_x = 0
        self.pan_start_y = 0

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # PASEK GÓRNY
        header = ctk.CTkFrame(self, height=50, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))

        ctk.CTkButton(header, text="< Wróć do listy", width=100, command=self.close_callback).pack(side="left",
                                                                                                   padx=(0, 20))
        ctk.CTkLabel(header, text=f"📍 Workflow: {self.model.title}", font=st.FONT_TITLE).pack(side="left")
        ctk.CTkButton(header, text="💾 Zapisz", width=100, fg_color="green", hover_color="darkgreen",
                      command=self.save_workflow).pack(side="right", padx=(10, 0))
        ctk.CTkButton(header, text="🗑️ Wyczyść", width=100, fg_color="#8b0000", hover_color="#5c0000",
                      command=self.clear_canvas).pack(side="right")

        # PASEK BOCZNY
        self.toolbar = ctk.CTkFrame(self, width=160)
        self.toolbar.grid(row=1, column=0, sticky="ns", padx=(20, 10), pady=(0, 20))
        ctk.CTkLabel(self.toolbar, text="Narzędzia", font=st.FONT_TITLE).pack(pady=(15, 20))

        self.current_mode = tk.StringVar(value="move")
        tools = [
            ("🖱️ Przesuwaj", "move"),
            ("✋ Przesuń Widok", "pan"),
            ("🔲 Dodaj Blok", "add_block"),
            ("📝 Dodaj Notatkę", "add_note"),
            ("↗️ Połącz", "add_edge"),
            ("🪢 Wyginaj Linie", "bend"),  # NOWE NARZĘDZIE
            ("❌ Usuń element", "delete")
        ]

        for text, mode in tools:
            rb = ctk.CTkRadioButton(
                self.toolbar, text=text, variable=self.current_mode, value=mode,
                font=("Helvetica", 13), command=self.on_tool_changed
            )
            rb.pack(anchor="w", padx=15, pady=8)

        zoom_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        zoom_frame.pack(side="bottom", pady=(5, 10))
        ctk.CTkButton(zoom_frame, text="-", width=30, command=self.zoom_out).pack(side="left", padx=2)
        self.zoom_lbl = ctk.CTkLabel(zoom_frame, text="100%", font=("Helvetica", 12, "bold"), width=45)
        self.zoom_lbl.pack(side="left", padx=2)
        ctk.CTkButton(zoom_frame, text="+", width=30, command=self.zoom_in).pack(side="left", padx=2)

        ctk.CTkButton(self.toolbar, text="🏠 Zresetuj Widok", width=120, command=self.reset_view).pack(side="bottom",
                                                                                                      pady=10)
        self.coord_lbl = ctk.CTkLabel(self.toolbar, text="X: 0 | Y: 0", text_color="gray", font=("Helvetica", 10))
        self.coord_lbl.pack(side="bottom", pady=5)

        # PŁÓTNO
        self.canvas_container = ctk.CTkFrame(self)
        self.canvas_container.grid(row=1, column=1, sticky="nsew", padx=(0, 20), pady=(0, 20))

        self.canvas = tk.Canvas(self.canvas_container, bg="#1a1a1a", highlightthickness=0,
                                scrollregion=(-10000, -10000, 10000, 10000))
        self.canvas.pack(fill="both", expand=True, padx=2, pady=2)

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

        self.after(50, self.initial_center)
        self.after(100, self.load_workflow)

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

    def initial_center(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        frac_x = (10000 - w / 2) / 20000 if w > 0 else 0.48
        frac_y = (10000 - h / 2) / 20000 if h > 0 else 0.48
        self.canvas.xview_moveto(frac_x)
        self.canvas.yview_moveto(frac_y)

    def reset_view(self):
        self.set_zoom(1.0)
        self.initial_center()

    def on_canvas_configure(self, event):
        self.draw_grid()

    def start_pan(self, event):
        self.canvas.config(cursor="fleur")
        self.canvas.scan_mark(event.x, event.y)

    def do_pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.draw_grid()
        self.on_tool_changed()

    def on_mouse_move(self, event):
        logical_x = int(self.canvas.canvasx(event.x) / self.zoom)
        logical_y = int(self.canvas.canvasy(event.y) / self.zoom)
        self.coord_lbl.configure(text=f"X: {logical_x} | Y: {logical_y}")

    def draw_grid(self, event=None):
        self.canvas.delete("grid")
        step = int(GRID_SIZE * self.zoom)
        if step < 5: return

        x0 = int(self.canvas.canvasx(0))
        y0 = int(self.canvas.canvasy(0))
        x1 = int(self.canvas.canvasx(self.canvas.winfo_width()))
        y1 = int(self.canvas.canvasy(self.canvas.winfo_height()))

        start_x = x0 - (x0 % step)
        start_y = y0 - (y0 % step)

        for i in range(start_x, x1 + step, step):
            self.canvas.create_line(i, y0, i, y1, fill="#252525", tags="grid")
        for i in range(start_y, y1 + step, step):
            self.canvas.create_line(x0, i, x1, i, fill="#252525", tags="grid")
        self.canvas.tag_lower("grid")

    def on_tool_changed(self):
        mode = self.current_mode.get()
        if mode == "add_edge":
            self.canvas.configure(cursor="crosshair")
        elif mode == "delete":
            self.canvas.configure(cursor="pirate")
        elif mode in ["add_block", "add_note"]:
            self.canvas.configure(cursor="plus")
        elif mode == "pan":
            self.canvas.configure(cursor="hand2")
        elif mode == "bend":
            self.canvas.configure(cursor="pencil")  # Kursor modyfikacji linii
        else:
            self.canvas.configure(cursor="arrow")

    def on_press(self, event):
        mode = self.current_mode.get()
        if mode == "pan":
            self.start_pan(event)
            return

        logical_x = self.canvas.canvasx(event.x) / self.zoom
        logical_y = self.canvas.canvasy(event.y) / self.zoom
        item = self.canvas.find_withtag("current")

        if mode in ["add_block", "add_note"]:
            dialog = ctk.CTkInputDialog(text="Wpisz nazwę:", title="Nowy element")
            text = dialog.get_input()
            if text:
                node_type = "block" if mode == "add_block" else "note"
                new_node = CanvasNode(self, snap(logical_x), snap(logical_y), text, node_type)
                self.nodes[new_node.id] = new_node

        elif mode == "move":
            clicked_node_id = None
            clicked_handle_id = None

            if item:
                tags = self.canvas.gettags(item[0])
                if "node" in tags and len(tags) > 1:
                    clicked_node_id = tags[1]
                elif "handle" in tags and len(tags) > 1:
                    clicked_handle_id = tags[1]
                # Złapanie punktu kontrolnego linii
                elif "waypoint" in tags and len(tags) > 2:
                    edge_id, wp_idx = tags[1], int(tags[2])
                    self.dragged_waypoint = (self.edges.get(edge_id), wp_idx)

            for n in self.nodes.values():
                n.set_selected(n.id == clicked_node_id or n.id == clicked_handle_id)

            if clicked_handle_id:
                self.resizing_node = self.nodes.get(clicked_handle_id)
            elif clicked_node_id:
                self.dragged_node = self.nodes.get(clicked_node_id)

        elif mode == "bend" and item:
            tags = self.canvas.gettags(item[0])
            # 1. Usunięcie istniejącego zakrętu (jeśli kliknęliśmy w żółtą kropkę)
            if "waypoint" in tags and len(tags) > 2:
                edge_id, wp_idx = tags[1], int(tags[2])
                edge = self.edges.get(edge_id)
                if edge:
                    edge.waypoints.pop(wp_idx)
                    edge.draw()
                    self.save_workflow()
            # 2. Dodanie nowego zakrętu na linii (jeśli kliknęliśmy w szarą linię)
            elif "edge" in tags and len(tags) > 1:
                edge_id = tags[1]
                edge = self.edges.get(edge_id)
                if edge:
                    insert_idx = edge.get_closest_segment_index(logical_x, logical_y)
                    edge.waypoints.insert(insert_idx, [snap(logical_x), snap(logical_y)])
                    edge.draw()
                    self.save_workflow()

        elif mode == "add_edge" and item:
            tags = self.canvas.gettags(item[0])
            if "node" in tags and len(tags) > 1:
                self.edge_start_node = self.nodes.get(tags[1])
                if self.edge_start_node:
                    self.temp_line = self.canvas.create_line(
                        self.edge_start_node.x * self.zoom, self.edge_start_node.y * self.zoom,
                        logical_x * self.zoom, logical_y * self.zoom,
                        dash=(5, 5), fill="yellow", width=2
                    )

        elif mode == "delete" and item:
            tags = self.canvas.gettags(item[0])
            if "node" in tags and len(tags) > 1:
                node_id = tags[1]
                if node_id in self.nodes:
                    self.nodes[node_id].destroy()
                    del self.nodes[node_id]
                    edges_to_delete = [e_id for e_id, e in self.edges.items() if
                                       e.source.id == node_id or e.target.id == node_id]
                    for e_id in edges_to_delete:
                        self.edges[e_id].destroy()
                        del self.edges[e_id]

            elif "edge" in tags and len(tags) > 1:
                edge_id = tags[1]
                if edge_id in self.edges:
                    self.edges[edge_id].destroy()
                    del self.edges[edge_id]

    def on_drag(self, event):
        mode = self.current_mode.get()
        if mode == "pan":
            self.do_pan(event)
            return

        logical_x = self.canvas.canvasx(event.x) / self.zoom
        logical_y = self.canvas.canvasy(event.y) / self.zoom

        if mode == "move":
            # Przesuwanie zakrętu na linii
            if getattr(self, "dragged_waypoint", None):
                edge, wp_idx = self.dragged_waypoint
                edge.waypoints[wp_idx] = [snap(logical_x), snap(logical_y)]
                edge.update_position()

            elif self.resizing_node:
                new_w = snap((logical_x - self.resizing_node.x) * 2)
                new_h = snap((logical_y - self.resizing_node.y) * 2)
                self.resizing_node.resize(new_w, new_h)
                for edge in self.edges.values():
                    if edge.source == self.resizing_node or edge.target == self.resizing_node:
                        edge.update_position()

            elif self.dragged_node:
                self.dragged_node.move_to(snap(logical_x), snap(logical_y))
                for edge in self.edges.values():
                    if edge.source == self.dragged_node or edge.target == self.dragged_node:
                        edge.update_position()

        elif mode == "add_edge" and self.edge_start_node and self.temp_line:
            self.canvas.coords(self.temp_line, self.edge_start_node.x * self.zoom, self.edge_start_node.y * self.zoom,
                               logical_x * self.zoom, logical_y * self.zoom)

    def on_release(self, event):
        mode = self.current_mode.get()
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        if mode == "add_edge" and self.edge_start_node:
            items = self.canvas.find_overlapping(canvas_x - 2, canvas_y - 2, canvas_x + 2, canvas_y + 2)
            target_node = None
            for item in items:
                tags = self.canvas.gettags(item)
                if "node" in tags and len(tags) > 1:
                    node_id = tags[1]
                    target_node = self.nodes.get(node_id)
                    if target_node and target_node != self.edge_start_node:
                        break

            if target_node and target_node != self.edge_start_node:
                new_edge = CanvasEdge(self, self.edge_start_node, target_node)
                self.edges[new_edge.id] = new_edge

            if self.temp_line:
                self.canvas.delete(self.temp_line)
                self.temp_line = None
            self.edge_start_node = None

        self.dragged_node = None
        self.resizing_node = None

        # Jeśli upuszczono punkt zakrętu, warto zapisać stan do pliku JSON
        if getattr(self, "dragged_waypoint", None):
            self.dragged_waypoint = None
            self.save_workflow()

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

    def apply_node_edit(self, node, new_text, new_header, new_shape, new_color, new_width, new_height):
        node.update_properties(new_text, new_header, new_shape, new_color, new_width, new_height)
        for edge in self.edges.values():
            if edge.source == node or edge.target == node: edge.update_position()
        self.save_workflow()

    def duplicate_node(self, node):
        new_node = CanvasNode(
            self, snap(node.x + 40), snap(node.y + 40), node.text, node.node_type,
            color=node.color, width=node.width, height=node.height,
            shape=node.shape, header=node.header
        )
        self.nodes[new_node.id] = new_node
        self.save_workflow()

    def apply_edge_edit(self, edge, new_direction, new_color, new_dashed):
        edge.update_properties(new_direction, new_color, new_dashed)
        self.save_workflow()

    def save_workflow(self):
        self.model.workflow_data["nodes"] = [node.to_dict() for node in self.nodes.values()]
        self.model.workflow_data["edges"] = [edge.to_dict() for edge in self.edges.values()]
        self.manager.save_to_file()

    def load_workflow(self):
        saved_nodes = self.model.workflow_data.get("nodes", [])
        for nd in saved_nodes:
            node = CanvasNode(
                self, x=nd["x"], y=nd["y"], text=nd["text"],
                node_type=nd.get("type", "block"), node_id=nd["id"],
                color=nd.get("color"), width=nd.get("width", 160), height=nd.get("height", 80),
                shape=nd.get("shape", "rect"), header=nd.get("header", "")
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
                    waypoints=ed.get("waypoints", [])  # <--- Wczytywanie punktów łamania
                )
                self.edges[edge.id] = edge

    def clear_canvas(self):
        self.canvas.delete("all")
        self.nodes.clear()
        self.edges.clear()
        self.draw_grid()
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