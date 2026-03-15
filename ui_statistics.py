import customtkinter as ctk
import settings as st
from translations import tr


class StatCard(ctk.CTkFrame):
    def __init__(self, master, title, value, color, **kwargs):
        super().__init__(master, fg_color=("#e0e0e0", "#2a2a2a"), corner_radius=10, **kwargs)
        ctk.CTkLabel(self, text=title, font=("Helvetica", 14)).pack(pady=(15, 5))
        ctk.CTkLabel(self, text=str(value), font=("Helvetica", 36, "bold"), text_color=color).pack(pady=(0, 15))


class StatisticsView(ctk.CTkFrame):
    def __init__(self, master, manager, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.manager = manager
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.build_ui()

    def build_ui(self):
        self.kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_frame.grid(row=0, column=0, sticky="ew", pady=20, padx=20)
        for i in range(4): self.kpi_frame.grid_columnconfigure(i, weight=1)

        self.details_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.details_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.details_frame.grid_columnconfigure((0, 1), weight=1)

        self.prio_frame = ctk.CTkFrame(self.details_frame, corner_radius=10)
        self.prio_frame.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        self.prio_lbl = ctk.CTkLabel(self.prio_frame, text="", font=st.FONT_TITLE)
        self.prio_lbl.pack(pady=15)
        self.prio_container = ctk.CTkFrame(self.prio_frame, fg_color="transparent")
        self.prio_container.pack(fill="both", expand=True, padx=20, pady=10)

        self.tasks_frame = ctk.CTkFrame(self.details_frame, corner_radius=10)
        self.tasks_frame.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        self.tasks_lbl = ctk.CTkLabel(self.tasks_frame, text="", font=st.FONT_TITLE)
        self.tasks_lbl.pack(pady=15)
        self.tasks_container = ctk.CTkFrame(self.tasks_frame, fg_color="transparent")
        self.tasks_container.pack(fill="both", expand=True, padx=20, pady=10)

    def refresh_data(self):
        tiles = [t for t in self.manager.tiles if not getattr(t, "is_archived", False)]
        total = len(tiles)
        completed = sum(1 for t in tiles if t.is_completed)
        active = total - completed
        overdue = sum(1 for t in tiles if not t.is_completed and t.days_left is not None and t.days_left < 0)

        for w in self.kpi_frame.winfo_children(): w.destroy()
        StatCard(self.kpi_frame, tr("stat_all"), total, ("#313131", "#ffffff")).grid(row=0, column=0, padx=10,
                                                                                     sticky="ew")
        StatCard(self.kpi_frame, tr("stat_active"), active, st.PRIORITY_COLORS["high"][1]).grid(row=0, column=1,
                                                                                                padx=10, sticky="ew")
        StatCard(self.kpi_frame, tr("stat_done"), completed, st.PRIORITY_COLORS["low"][1]).grid(row=0, column=2,
                                                                                                padx=10, sticky="ew")
        StatCard(self.kpi_frame, tr("stat_overdue"), overdue, st.PRIORITY_COLORS["very-high"][1]).grid(row=0, column=3,
                                                                                                       padx=10,
                                                                                                       sticky="ew")

        self.prio_lbl.configure(text=tr("stat_prio_dist"))
        for w in self.prio_container.winfo_children(): w.destroy()

        prio_counts = {"very-high": 0, "high": 0, "medium": 0, "low": 0, "without": 0}
        for t in tiles: prio_counts[t.priority] += 1

        for p_key, p_label in st.PRIORITY_LABELS.items():
            count = prio_counts[p_key]
            row = ctk.CTkFrame(self.prio_container, fg_color="transparent")
            row.pack(fill="x", pady=12)
            # ZMIANA: Tłumaczenie napisów z settings.py
            ctk.CTkLabel(row, text=tr(p_label), width=120, anchor="w", font=("Helvetica", 13, "bold")).pack(side="left")
            val = count / total if total > 0 else 0
            bar = ctk.CTkProgressBar(row, height=14, progress_color=st.PRIORITY_COLORS[p_key][1],
                                     fg_color=("#d0d0d0", "#333333"))
            bar.pack(side="left", fill="x", expand=True, padx=15)
            bar.set(val)
            ctk.CTkLabel(row, text=str(count), width=30, font=("Helvetica", 13, "bold")).pack(side="right")

        self.tasks_lbl.configure(text=tr("stat_tasks_global"))
        for w in self.tasks_container.winfo_children(): w.destroy()

        total_tasks = 0
        done_tasks = 0
        for t in tiles:
            todos = t.content.get("todos", [])
            total_tasks += len(todos)
            done_tasks += sum(1 for todo in todos if todo.get("is_done"))

        tasks_val = done_tasks / total_tasks if total_tasks > 0 else 0
        pct = int(tasks_val * 100)

        ctk.CTkLabel(self.tasks_container, text=tr("stat_tasks_total", total_tasks), font=("Helvetica", 13),
                     text_color="gray").pack(pady=(20, 10))
        t_bar = ctk.CTkProgressBar(self.tasks_container, height=30, progress_color="#4da6ff",
                                   fg_color=("#d0d0d0", "#333333"))
        t_bar.pack(fill="x", padx=40, pady=20)
        t_bar.set(tasks_val)
        ctk.CTkLabel(self.tasks_container, text=tr("stat_completed_pct", pct), font=("Helvetica", 48, "bold"),
                     text_color="#4da6ff").pack(pady=(10, 5))
        ctk.CTkLabel(self.tasks_container, text=tr("stat_checked", done_tasks, total_tasks),
                     font=("Helvetica", 14)).pack()