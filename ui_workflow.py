import customtkinter as ctk
import tkinter as tk
import settings as st
import math
import uuid
from datetime import datetime
from ui_dialogs import ExportDialog, NodeEditDialog, EdgeEditDialog
from translations import tr

try:
    from PIL import ImageGrab

    HAS_PIL = True
except ImportError:
    HAS_PIL = False

GRID_SIZE = 20


def snap(val):
    return round(val / 20) * 20


def darken_hex(hex_color, factor=0.7):
    if not hex_color or not isinstance(hex_color, str) or not hex_color.startswith("#") or len(hex_color) != 7:
        return "#1a1a1a"
    try:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        r = max(0, int(r * factor))
        g = max(0, int(g * factor))
        b = max(0, int(b * factor))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return "#1a1a1a"


def get_oval_points(x1, y1, x2, y2, steps=40):
    pts = []
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    rx, ry = (x2 - x1) / 2, (y2 - y1) / 2
    for i in range(steps):
        angle = -math.pi / 2 + 2 * math.pi * i / steps
        pts.append((cx + rx * math.cos(angle), cy + ry * math.sin(angle)))
    return pts


def get_rounded_rect_points_exact(x1, y1, x2, y2, r, steps=10):
    pts = []
    r = min(r, (x2 - x1) / 2, (y2 - y1) / 2)
    for i in range(steps + 1):
        angle = -math.pi / 2 + (math.pi / 2) * (i / steps)
        pts.append((x2 - r + r * math.cos(angle), y1 + r + r * math.sin(angle)))
    for i in range(steps + 1):
        angle = 0 + (math.pi / 2) * (i / steps)
        pts.append((x2 - r + r * math.cos(angle), y2 - r + r * math.sin(angle)))
    for i in range(steps + 1):
        angle = math.pi / 2 + (math.pi / 2) * (i / steps)
        pts.append((x1 + r + r * math.cos(angle), y2 - r + r * math.sin(angle)))
    for i in range(steps + 1):
        angle = math.pi + (math.pi / 2) * (i / steps)
        pts.append((x1 + r + r * math.cos(angle), y1 + r + r * math.sin(angle)))
    return pts


def clip_polygon_top(pts, sep_y):
    clipped = []
    if not pts: return clipped
    for i in range(len(pts)):
        p1 = pts[i]
        p2 = pts[(i + 1) % len(pts)]
        if p1[1] <= sep_y:
            clipped.append(p1)
            if p2[1] > sep_y:
                t = (sep_y - p1[1]) / (p2[1] - p1[1]) if p2[1] != p1[1] else 0
                ix = p1[0] + t * (p2[0] - p1[0])
                clipped.append((ix, sep_y))
        else:
            if p2[1] <= sep_y:
                t = (sep_y - p1[1]) / (p2[1] - p1[1]) if p2[1] != p1[1] else 0
                ix = p1[0] + t * (p2[0] - p1[0])
                clipped.append((ix, sep_y))
    return clipped


def get_key(d, val, default):
    for k, v in d.items():
        if v == val: return k
    return default


class CanvasNode:
    def __init__(self, wf, x, y, text, node_type="block", node_id=None, color=None, border_color=None, border_width=2,
                 width=160, height=80, shape="rect", header="", priority="medium", deadline="", tags="",
                 show_days_left=False, group_id=None,
                 font_family="Helvetica", font_size=12, font_color=None,
                 header_font_family="Helvetica", header_font_size=10, header_font_color=None,
                 tags_font_family="Helvetica", tags_font_size=10, tags_font_color=None,
                 date_font_family="Helvetica", date_font_size=10, date_font_color=None):
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
        self.border_width = int(float(border_width))
        self.priority = priority
        self.deadline = deadline
        self.tags = tags
        self.show_days_left = show_days_left

        self.font_family = font_family
        self.font_size = int(float(font_size))
        self.font_color = font_color

        self.header_font_family = header_font_family
        self.header_font_size = int(float(header_font_size))
        self.header_font_color = header_font_color

        self.tags_font_family = tags_font_family
        self.tags_font_size = int(float(tags_font_size))
        self.tags_font_color = tags_font_color

        self.date_font_family = date_font_family
        self.date_font_size = int(float(date_font_size))
        self.date_font_color = date_font_color

        self.selected = False

        self.bg_id = None;
        self.text_id = None;
        self.header_id = None;
        self.handle_id = None
        self.proj_dot_id = None;
        self.proj_date_id = None;
        self.proj_tags_id = None
        self.header_bg_id = None;
        self.sep_line_id = None;
        self.outline_id = None
        self.draw()

    def bring_to_front(self):
        for item in [self.bg_id, getattr(self, 'header_bg_id', None), getattr(self, 'sep_line_id', None),
                     self.outline_id,
                     self.header_id, self.text_id, self.proj_dot_id, self.proj_tags_id, self.proj_date_id,
                     self.handle_id]:
            if item: self.canvas.tag_raise(item)

    def send_to_back(self):
        for item in [self.handle_id, self.proj_date_id, self.proj_tags_id, self.proj_dot_id, self.text_id,
                     self.header_id, self.outline_id, getattr(self, 'sep_line_id', None),
                     getattr(self, 'header_bg_id', None), self.bg_id]:
            if item: self.canvas.tag_lower(item)
        for e in self.wf.edges.values():
            self.canvas.tag_lower(e.line_id)
            if getattr(e, "label_bg_id", None): self.canvas.tag_lower(e.label_bg_id)
            if getattr(e, "label_id", None): self.canvas.tag_lower(e.label_id)
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

        base_f_size = max(4, int(self.font_size * z))
        font_style = (self.font_family, base_f_size, "bold")
        base_h_size = max(4, int(self.header_font_size * z))
        header_font_style = (self.header_font_family, base_h_size, "bold")

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
        l_width = max(1, int(self.border_width * z))

        if self.shape == "oval":
            pts = get_oval_points(x1, y1, x2, y2)
        elif self.shape == "diamond":
            pts = [(sx, y1), (x2, sy), (sx, y2), (x1, sy)]
        elif self.shape == "parallelogram":
            offset = sw * 0.15
            pts = [(x1 + offset, y1), (x2, y1), (x2 - offset, y2), (x1, y2)]
        elif self.shape == "hexagon":
            offset = sw * 0.15
            pts = [(x1 + offset, y1), (x2 - offset, y1), (x2, sy), (x2 - offset, y2), (x1 + offset, y2), (x1, sy)]
        elif self.shape == "trapezoid":
            offset = sw * 0.15
            pts = [(x1, y1), (x2, y1), (x2 - offset, y2), (x1 + offset, y2)]
        elif self.shape == "capsule":
            r = min(sw, sh) / 2
            pts = get_rounded_rect_points_exact(x1, y1, x2, y2, r)
        else:
            r = 12 * z
            pts = get_rounded_rect_points_exact(x1, y1, x2, y2, r)

        flat_pts = [coord for p in pts for coord in p]
        self.bg_id = self.canvas.create_polygon(flat_pts, fill=bg, outline="", tags=("node", self.id))

        header_height = 0
        wrap_w = sw - 20 * z
        if self.shape in ["diamond", "oval", "hexagon"]:
            wrap_w = sw * 0.65
        elif self.shape in ["parallelogram", "trapezoid"]:
            wrap_w = sw * 0.75

        # 1. NAGŁÓWEK (Mierzony od góry y1)
        if self.header:
            max_h_lines = max(1, int((sh * 0.4) / (base_h_size * 1.2)))
            h_chars_per_line = max(5, int(wrap_w / (base_h_size * 0.6)))
            max_h_chars = h_chars_per_line * max_h_lines
            header_display = self.header[:max_h_chars - 3] + "..." if len(self.header) > max_h_chars else self.header

            header_y = y1 + base_h_size + (6 * z)
            temp_id = self.canvas.create_text(sx, header_y, text=header_display, font=header_font_style, width=wrap_w)
            bbox = self.canvas.bbox(temp_id)
            if bbox:
                header_height = bbox[3] - bbox[1] + (12 * z)
            else:
                header_height = base_h_size * 2 + (12 * z)
            self.canvas.delete(temp_id)

            header_height = min(header_height, sh * 0.6)
            sep_y = y1 + header_height

            clipped_pts = clip_polygon_top(pts, sep_y)
            if clipped_pts:
                flat_clipped = [coord for p in clipped_pts for coord in p]
                dark_bg = darken_hex(bg, 0.7)
                self.header_bg_id = self.canvas.create_polygon(flat_clipped, fill=dark_bg, outline="",
                                                               tags=("node", self.id))

            sep_points = [p for p in clipped_pts if abs(p[1] - sep_y) < 1e-4]
            if len(sep_points) >= 2:
                sep_points.sort(key=lambda p: p[0])
                self.sep_line_id = self.canvas.create_line(sep_points[0][0], sep_y, sep_points[-1][0], sep_y,
                                                           fill=outline_color, width=l_width, tags=("node", self.id))

            if self.header_font_color:
                header_color = self.header_font_color
            else:
                header_color = "#555555" if bg in ["#ffffff", "#e6c280", "#888888"] else "#dddddd"

            self.header_id = self.canvas.create_text(sx, header_y, text=header_display, fill=header_color,
                                                     font=header_font_style, width=wrap_w, justify="center",
                                                     tags=("node", self.id))

        self.outline_id = self.canvas.create_polygon(flat_pts, fill="", outline=outline_color, width=l_width,
                                                     tags=("node", self.id))

        # 2. SEKCJA DOLNA (Mierzona od dołu y2 w górę, co zapobiega wychodzeniu za blok)
        bottom_y = y2 - 8 * z

        if self.node_type == "project":
            dot_c = st.PRIORITY_COLORS.get(self.priority, ("gray", "gray"))[1]
            pr = max(2, int(4 * z))
            px, py = x2 - 12 * z, bottom_y - pr
            self.proj_dot_id = self.canvas.create_oval(px - pr, py - pr, px + pr, py + pr, fill=dot_c, outline=dot_c,
                                                       tags=("node", self.id))

            if self.deadline:
                dl_color = self.date_font_color if self.date_font_color else "#aaaaaa"
                days_text = ""
                try:
                    d_date = datetime.strptime(self.deadline, "%Y-%m-%d").date()
                    dl = (d_date - datetime.now().date()).days

                    if not self.date_font_color:
                        if dl < 0:
                            dl_color = st.TIME_COLORS["overdue"][1]
                        elif dl == 0:
                            dl_color = st.TIME_COLORS["today"][1]
                        elif dl == 1:
                            dl_color = st.TIME_COLORS["1_3"][1]
                        elif dl <= 14:
                            dl_color = st.TIME_COLORS["8_14"][1]
                        else:
                            dl_color = st.TIME_COLORS["15_plus"][1]

                    if self.show_days_left:
                        if sw > 180 * z:
                            if dl < 0:
                                days_text = tr("wf_overdue", -dl)
                            elif dl == 0:
                                days_text = tr("wf_today")
                            elif dl == 1:
                                days_text = tr("wf_tomorrow")
                            else:
                                days_text = tr("wf_days_left", dl)
                        else:
                            days_text = f" ({dl}d)"
                except ValueError:
                    pass

                date_str = f"⏱ {self.deadline}{days_text}"
                date_font_style = (self.date_font_family, max(4, int(self.date_font_size * z)), "bold")

                self.proj_date_id = self.canvas.create_text(x1 + 10 * z, bottom_y, text=date_str, fill=dl_color,
                                                            font=date_font_style, anchor="sw", tags=("node", self.id))
                bbox_d = self.canvas.bbox(self.proj_date_id)
                if bbox_d:
                    bottom_y -= (bbox_d[3] - bbox_d[1] + 4 * z)
                else:
                    bottom_y -= (self.date_font_size * z + 4 * z)

            if self.tags:
                tags_font_style = (self.tags_font_family, max(4, int(self.tags_font_size * z)), "italic")
                t_col = self.tags_font_color if self.tags_font_color else "#4da6ff"
                self.proj_tags_id = self.canvas.create_text(x1 + 10 * z, bottom_y, text=" ".join(
                    [f"#{t.strip()}" for t in self.tags.split(",")]), fill=t_col, font=tags_font_style, width=wrap_w,
                                                            anchor="sw", tags=("node", self.id))
                bbox_t = self.canvas.bbox(self.proj_tags_id)
                if bbox_t:
                    bottom_y -= (bbox_t[3] - bbox_t[1] + 4 * z)
                else:
                    bottom_y -= (self.tags_font_size * z + 4 * z)

        # 3. GŁÓWNY TEKST (Otrzymuje resztę miejsca dostępną w środku)
        if self.font_color:
            text_color = self.font_color
        else:
            text_color = "black" if bg in ["#ffffff", "#e6c280", "#888888"] else "#DCE4EE"

        sep_y_final = y1 + header_height
        available_h = bottom_y - sep_y_final - (6 * z) if self.node_type == "project" else sh - header_height - (10 * z)

        display_text = self.text
        if available_h < base_f_size:
            display_text = ""
        elif self.text:
            chars_per_line = max(5, int(wrap_w / (base_f_size * 0.6)))
            max_lines = max(1, int(available_h / (base_f_size * 1.2)))
            max_chars = chars_per_line * max_lines
            display_text = self.text[:max_chars - 3] + "..." if len(self.text) > max_chars else self.text

        if self.node_type == "project":
            # PADDING DLA KLOCKÓW PROJEKTOWYCH NA PŁÓTNIE
            padding_y = 12 * z  # <--- TUTAJ ZWIĘKSZ/ZMNIEJSZ (np. z 4 na 12), by odsunąć tekst od linii
            text_y = sep_y_final + padding_y
            self.text_id = self.canvas.create_text(x1 + 10 * z, text_y, text=display_text, fill=text_color,
                                                   font=font_style, width=wrap_w, anchor="nw", tags=("node", self.id))
        else:
            # CENTROWANIE DLA ZWYKŁYCH KLOCKÓW (Romb, Elipsa)
            if self.shape in ["diamond", "oval", "hexagon"] and self.header:
                # Najszersze miejsce rombu to środek (sy). Ściągamy tekst wyżej, by nie wpadł w wąski dół!
                text_y = max(sy + (4 * z), sep_y_final + (8 * z))
            else:
                # Zwykłe centrowanie dla prostokątów
                text_y = sep_y_final + (available_h / 2) + (5 * z)

            self.text_id = self.canvas.create_text(sx, text_y, text=display_text, fill=text_color, font=font_style,
                                                   width=wrap_w, justify="center", tags=("node", self.id))

        self.handle_id = self.canvas.create_rectangle(x2 - 12 * z, y2 - 12 * z, x2, y2, fill="white", outline="#333",
                                                      tags=("handle", self.id),
                                                      state="normal" if self.selected else "hidden")

    def clear_graphics(self):
        for item in [self.bg_id, getattr(self, 'header_bg_id', None), getattr(self, 'sep_line_id', None),
                     self.outline_id, self.text_id, self.header_id, self.handle_id, self.proj_dot_id, self.proj_date_id,
                     self.proj_tags_id]:
            if item: self.canvas.delete(item)

    def move_to(self, x, y):
        self.x = x;
        self.y = y;
        self.draw()

    def resize(self, w, h):
        self.width = max(50, w);
        self.height = max(30, h);
        self.draw()

    def set_selected(self, state):
        self.selected = state;
        self.draw()

    def update_properties(self, data):
        self.text = data.get("text", self.text);
        self.header = data.get("header", self.header)
        self.shape = data.get("shape", self.shape);
        self.node_type = data.get("node_type", data.get("type", self.node_type))
        self.color = data.get("color", self.color);
        self.border_color = data.get("border_color", self.border_color)
        self.border_width = int(data.get("border_width", self.border_width))
        self.priority = data.get("priority", "medium");
        self.deadline = data.get("deadline", "")
        self.tags = data.get("tags", "");
        self.show_days_left = data.get("show_days_left", False)

        self.font_family = data.get("font_family", "Helvetica")
        self.font_size = int(data.get("font_size", 12))
        self.font_color = data.get("font_color", None)

        self.header_font_family = data.get("header_font_family", "Helvetica")
        self.header_font_size = int(data.get("header_font_size", 10))
        self.header_font_color = data.get("header_font_color", None)

        self.tags_font_family = data.get("tags_font_family", "Helvetica")
        self.tags_font_size = int(data.get("tags_font_size", 10))
        self.tags_font_color = data.get("tags_font_color", None)

        self.date_font_family = data.get("date_font_family", "Helvetica")
        self.date_font_size = int(data.get("date_font_size", 10))
        self.date_font_color = data.get("date_font_color", None)

        self.resize(data.get("width", self.width), data.get("height", self.height));
        self.draw()

    def destroy(self):
        self.clear_graphics()

    def to_dict(self):
        return {
            "id": self.id, "x": self.x, "y": self.y, "text": self.text, "header": self.header,
            "type": self.node_type, "shape": self.shape, "color": self.color,
            "border_color": getattr(self, 'border_color', None),
            "border_width": self.border_width,
            "width": self.width, "height": self.height, "priority": getattr(self, 'priority', 'medium'),
            "deadline": getattr(self, 'deadline', ''), "tags": getattr(self, 'tags', ''),
            "show_days_left": getattr(self, 'show_days_left', False), "group_id": self.group_id,
            "font_family": self.font_family, "font_size": self.font_size, "font_color": self.font_color,
            "header_font_family": self.header_font_family, "header_font_size": self.header_font_size,
            "header_font_color": self.header_font_color,
            "tags_font_family": self.tags_font_family, "tags_font_size": self.tags_font_size,
            "tags_font_color": self.tags_font_color,
            "date_font_family": self.date_font_family, "date_font_size": self.date_font_size,
            "date_font_color": self.date_font_color
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
        if getattr(self, "line_id", None): self.canvas.delete(self.line_id)
        if getattr(self, "label_id", None): self.canvas.delete(self.label_id)
        if getattr(self, "label_bg_id", None): self.canvas.delete(self.label_bg_id)
        for hid in getattr(self, "handle_ids", []): self.canvas.delete(hid)
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
        self.selected = state;
        self.update_position()

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

        header = ctk.CTkFrame(self, height=50, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))
        ctk.CTkButton(header, text=tr("back_to_list"), width=100, command=self.close_callback).pack(side="left",
                                                                                                    padx=(0, 20))
        ctk.CTkLabel(header, text=f"📍 Workflow: {self.model.title}", font=st.FONT_TITLE).pack(side="left")

        self.coord_lbl = ctk.CTkLabel(header, text="X: 0 | Y: 0", text_color="gray", font=("Helvetica", 12, "bold"))
        self.coord_lbl.pack(side="right", padx=(20, 0))

        ctk.CTkButton(header, text=tr("btn_help"), width=70, fg_color="#1f538d", command=self.show_help).pack(
            side="right", padx=(10, 0))

        if HAS_PIL: ctk.CTkButton(header, text=tr("btn_export"), width=100, fg_color="#1f538d",
                                  command=self.export_image).pack(side="right", padx=(10, 0))
        self.save_btn = ctk.CTkButton(header, text=tr("btn_save"), width=100, fg_color="green", hover_color="darkgreen",
                                      command=self.save_workflow)
        self.save_btn.pack(side="right", padx=(10, 0))
        ctk.CTkButton(header, text=tr("btn_clear"), width=100, fg_color="#8b0000", hover_color="#5c0000",
                      command=self.clear_canvas).pack(side="right")

        self.toolbar = ctk.CTkFrame(self, width=180)
        self.toolbar.grid(row=1, column=0, sticky="ns", padx=(20, 10), pady=(0, 20))

        self.toolbar_bottom = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        self.toolbar_bottom.pack(side="bottom", fill="x", pady=5)

        ctk.CTkButton(self.toolbar_bottom, text=tr("reset_view"), width=120, command=self.reset_view).pack(
            side="bottom", pady=10)

        zoom_frame = ctk.CTkFrame(self.toolbar_bottom, fg_color="transparent")
        zoom_frame.pack(side="bottom", pady=(5, 10))
        ctk.CTkButton(zoom_frame, text="-", width=30, command=self.zoom_out).pack(side="left", padx=2)
        self.zoom_lbl = ctk.CTkLabel(zoom_frame, text="100%", font=("Helvetica", 12, "bold"), width=45)
        self.zoom_lbl.pack(side="left", padx=2)
        ctk.CTkButton(zoom_frame, text="+", width=30, command=self.zoom_in).pack(side="left", padx=2)

        bg_frame = ctk.CTkFrame(self.toolbar_bottom, fg_color="transparent")
        bg_frame.pack(side="bottom", pady=10)
        ctk.CTkLabel(bg_frame, text=tr("bg_color_wf"), font=("Helvetica", 10)).pack()
        self.canvas_bg_var = ctk.StringVar()

        loaded_bg = self.model.workflow_data.get("canvas_bg", "#1a1a1a")
        current_bg_key = get_key(st.WORKFLOW_BG_COLORS, loaded_bg, list(st.WORKFLOW_BG_COLORS.keys())[0])
        self.canvas_bg_var.set(tr(current_bg_key))
        ctk.CTkOptionMenu(bg_frame, values=[tr(k) for k in st.WORKFLOW_BG_COLORS.keys()], variable=self.canvas_bg_var,
                          command=self.change_canvas_bg, width=120).pack(pady=2)

        self.toolbar_scroll = ctk.CTkScrollableFrame(self.toolbar, fg_color="transparent", width=170)
        self.toolbar_scroll.pack(side="top", fill="both", expand=True)

        ctk.CTkLabel(self.toolbar_scroll, text=tr("tools"), font=st.FONT_TITLE).pack(pady=(10, 10))

        self.current_mode = tk.StringVar(value="move")
        tools = [(tr("tool_move"), "move"), (tr("tool_pan"), "pan"), (tr("tool_add_block"), "add_block"),
                 (tr("tool_add_edge"), "add_edge"), (tr("tool_bend"), "bend"), (tr("tool_delete"), "delete")]
        for text, mode in tools:
            rb = ctk.CTkRadioButton(self.toolbar_scroll, text=text, variable=self.current_mode, value=mode,
                                    font=("Helvetica", 13), command=self.on_tool_changed)
            rb.pack(anchor="w", padx=10, pady=8)

        self.context_frame = ctk.CTkFrame(self.toolbar_scroll, fg_color="transparent")
        self.context_frame.pack(fill="x", padx=5, pady=5)

        self.block_options = ctk.CTkFrame(self.context_frame, fg_color="transparent")
        ctk.CTkLabel(self.block_options, text=tr("block_type"), font=("Helvetica", 11)).pack()
        self.new_node_type = ctk.StringVar(value=tr(list(st.NODE_TYPES.keys())[0]))
        ctk.CTkOptionMenu(self.block_options, values=[tr(k) for k in st.NODE_TYPES.keys()], variable=self.new_node_type,
                          width=120).pack(pady=2)

        self.edge_options = ctk.CTkFrame(self.context_frame, fg_color="transparent")
        ctk.CTkLabel(self.edge_options, text=tr("arrow_type"), font=("Helvetica", 11)).pack(pady=(0, 2))
        self.new_edge_dir = ctk.StringVar(value=tr(list(st.EDGE_DIRECTIONS.keys())[0]))
        ctk.CTkOptionMenu(self.edge_options, values=[tr(k) for k in st.EDGE_DIRECTIONS.keys()],
                          variable=self.new_edge_dir, width=120).pack(pady=2)

        ctk.CTkLabel(self.edge_options, text=tr("line_color"), font=("Helvetica", 11)).pack(pady=(5, 2))
        self.new_edge_color = ctk.StringVar(value=tr(list(st.EDGE_COLORS.keys())[0]))
        ctk.CTkOptionMenu(self.edge_options, values=[tr(k) for k in st.EDGE_COLORS.keys()],
                          variable=self.new_edge_color, width=120).pack(pady=2)

        ctk.CTkLabel(self.edge_options, text=tr("line_thickness"), font=("Helvetica", 11)).pack(pady=(5, 2))
        self.new_edge_width = ctk.StringVar(value="2")
        ctk.CTkOptionMenu(self.edge_options, values=st.EDGE_WIDTHS, variable=self.new_edge_width, width=120).pack(
            pady=2)
        self.new_edge_dashed = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.edge_options, text=tr("dashed_line"), variable=self.new_edge_dashed).pack(pady=10)

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
        from translations import rev_tr
        act_key = rev_tr(choice, list(st.WORKFLOW_BG_COLORS.keys()))
        c = st.WORKFLOW_BG_COLORS.get(act_key, "#1a1a1a")
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

    def show_help(self):
        from ui_dialogs import HelpDialog
        HelpDialog(self, context="workflow")

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
            tk.messagebox.showinfo(tr("export_title"), tr("export_success"))
        except Exception as e:
            tk.messagebox.showerror("Error", tr("export_error", e))
        finally:
            self.canvas.config(bg=old_bg)
            self.canvas.itemconfig("grid", state="normal")
            self.minimap.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)

    def mark_unsaved(self):
        if not self.has_unsaved_changes:
            self.has_unsaved_changes = True
            self.save_btn.configure(fg_color="#d47300", hover_color="#a35800", text=tr("btn_save_star"))

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
                border_width=n_data.get("border_width", 2),
                width=n_data["width"], height=n_data["height"], shape=n_data["shape"], header=n_data["header"],
                priority=n_data.get("priority", "medium"), deadline=n_data.get("deadline", ""),
                tags=n_data.get("tags", ""),
                show_days_left=n_data.get("show_days_left", False), group_id=n_data.get("group_id"),
                font_family=n_data.get("font_family", "Helvetica"), font_size=n_data.get("font_size", 12),
                font_color=n_data.get("font_color"),
                header_font_family=n_data.get("header_font_family", "Helvetica"),
                header_font_size=n_data.get("header_font_size", 10), header_font_color=n_data.get("header_font_color"),
                tags_font_family=n_data.get("tags_font_family", "Helvetica"),
                tags_font_size=n_data.get("tags_font_size", 10), tags_font_color=n_data.get("tags_font_color"),
                date_font_family=n_data.get("date_font_family", "Helvetica"),
                date_font_size=n_data.get("date_font_size", 10), date_font_color=n_data.get("date_font_color")
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
                    color=st.EDGE_COLORS.get(get_key(st.EDGE_COLORS, e_data.get("color"), "Szary (Domyślny)")),
                    dashed=e_data.get("dashed", False),
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
        self.update_idletasks()
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        frac_x = (10000 - w / 2) / 20000 if w > 0 else 0.48
        frac_y = (10000 - h / 2) / 20000 if h > 0 else 0.48
        self.canvas.xview_moveto(frac_x)
        self.canvas.yview_moveto(frac_y)
        self.update_minimap()
        self.draw_grid()

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
            from translations import rev_tr
            dialog = ctk.CTkInputDialog(text=tr("enter_name"), title=tr("new_element"))
            text = dialog.get_input()
            if text:
                act_type = rev_tr(self.new_node_type.get(), list(st.NODE_TYPES.keys()))
                ntype = st.NODE_TYPES.get(act_type, "block")
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
                    self.resizing_node = self.nodes.get(clicked_handle_id)
                    self.resize_start_w = self.resizing_node.width
                    self.resize_start_h = self.resizing_node.height
                elif "waypoint" in tags and len(tags) > 2:
                    edge_id, wp_idx = tags[1], int(tags[2])
                    self.dragged_waypoint = (self.edges.get(edge_id), wp_idx)
                elif "edge" in tags and len(tags) > 1:
                    clicked_edge_id = tags[1]
                elif "edge_label" in tags and len(tags) > 1:
                    clicked_edge_id = tags[1]

            is_ctrl_pressed = (event.state & 0x0004) != 0

            if clicked_handle_id:
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
                        from translations import rev_tr
                        act_col = rev_tr(self.new_edge_color.get(), list(st.EDGE_COLORS.keys()))
                        act_dir = rev_tr(self.new_edge_dir.get(), list(st.EDGE_DIRECTIONS.keys()))
                        c = st.EDGE_COLORS.get(act_col, "#888888")
                        d = self.new_edge_dashed.get()
                        w = int(self.new_edge_width.get())
                        dir_val = st.EDGE_DIRECTIONS.get(act_dir, "last")

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
                    from translations import rev_tr
                    self.drawing_state = {"node": clicked_node, "waypoints": []}
                    act_col = rev_tr(self.new_edge_color.get(), list(st.EDGE_COLORS.keys()))
                    act_dir = rev_tr(self.new_edge_dir.get(), list(st.EDGE_DIRECTIONS.keys()))
                    c = st.EDGE_COLORS.get(act_col, "#888888")
                    d = (5, 5) if self.new_edge_dashed.get() else ""
                    w = int(self.new_edge_width.get())
                    dir_val = st.EDGE_DIRECTIONS.get(act_dir, "last")
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

            elif getattr(self, "resizing_node", None):
                new_w = (logical_x - self.resizing_node.x) * 2
                new_h = (logical_y - self.resizing_node.y) * 2

                if (event.state & 0x0001) != 0:
                    aspect = self.resize_start_w / self.resize_start_h if self.resize_start_h != 0 else 1
                    if new_w > new_h * aspect:
                        new_h = new_w / aspect
                    else:
                        new_w = new_h * aspect

                new_w = snap(new_w)
                new_h = snap(new_h)

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
            color=node.color, border_color=getattr(node, 'border_color', None),
            border_width=getattr(node, 'border_width', 2), width=node.width, height=node.height,
            shape=node.shape, header=node.header, priority=getattr(node, 'priority', 'medium'),
            deadline=getattr(node, 'deadline', ''), tags=getattr(node, 'tags', ''),
            show_days_left=getattr(node, 'show_days_left', False),
            group_id=getattr(node, 'group_id', None),
            font_family=node.font_family, font_size=node.font_size, font_color=node.font_color,
            header_font_family=node.header_font_family, header_font_size=node.header_font_size,
            header_font_color=node.header_font_color,
            tags_font_family=node.tags_font_family, tags_font_size=node.tags_font_size,
            tags_font_color=node.tags_font_color,
            date_font_family=node.date_font_family, date_font_size=node.date_font_size,
            date_font_color=node.date_font_color
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
        self.save_btn.configure(fg_color="green", hover_color="darkgreen", text=tr("btn_save"))

    def _render_current_state(self):
        saved_nodes = self.model.workflow_data.get("nodes", [])
        for nd in saved_nodes:
            node = CanvasNode(
                self, x=nd["x"], y=nd["y"], text=nd["text"],
                node_type=nd.get("type", "block"), node_id=nd["id"],
                color=nd.get("color"), border_color=nd.get("border_color"), border_width=nd.get("border_width", 2),
                width=nd.get("width", 160), height=nd.get("height", 80),
                shape=nd.get("shape", "rect"), header=nd.get("header", ""),
                priority=nd.get("priority", "medium"), deadline=nd.get("deadline", ""), tags=nd.get("tags", ""),
                show_days_left=nd.get("show_days_left", False), group_id=nd.get("group_id"),
                font_family=nd.get("font_family", "Helvetica"), font_size=nd.get("font_size", 12),
                font_color=nd.get("font_color"),
                header_font_family=nd.get("header_font_family", "Helvetica"),
                header_font_size=nd.get("header_font_size", 10), header_font_color=nd.get("header_font_color"),
                tags_font_family=nd.get("tags_font_family", "Helvetica"), tags_font_size=nd.get("tags_font_size", 10),
                tags_font_color=nd.get("tags_font_color"),
                date_font_family=nd.get("date_font_family", "Helvetica"), date_font_size=nd.get("date_font_size", 10),
                date_font_color=nd.get("date_font_color")
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