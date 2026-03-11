import customtkinter as ctk
import settings as st
from models import TileManager, ProjectTileModel
from ui import ProjectTileWidget, TileFormDialog

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")

class SmartProjectTilesApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(st.WINDOW_TITLE)
        self.geometry(f"{st.WINDOW_WIDTH}x{st.WINDOW_HEIGHT}")

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.setup_ui()

    def setup_ui(self):
        self.manager = TileManager()
        self.manager.load_from_file()

        # PASEK NARZĘDZI
        self.toolbar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        self.toolbar_frame.grid_columnconfigure(0, weight=1)

        self.add_btn = ctk.CTkButton(
            self.toolbar_frame,
            text="+ Dodaj Kafelek",
            font=st.FONT_TITLE,
            command=self.open_add_dialog
        )
        self.add_btn.grid(row=0, column=0, sticky="w")

        self.view_switcher = ctk.CTkSegmentedButton(
            self.toolbar_frame,
            values=["Lista", "Siatka (2)", "Siatka (3)"],
            command=self.change_view
        )
        self.view_switcher.set("Lista")
        self.view_switcher.grid(row=0, column=1, sticky="e")

        # RAMKA KAFELKÓW
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 20))

        self.draw_tiles(columns=1)

    def change_view(self, selected_value):
        if selected_value == "Lista":
            self.draw_tiles(columns=1)
        elif selected_value == "Siatka (2)":
            self.draw_tiles(columns=2)
        elif selected_value == "Siatka (3)":
            self.draw_tiles(columns=3)

    def open_add_dialog(self):
        dialog = TileFormDialog(master=self, on_save_callback=self.save_new_tile)

    def save_new_tile(self, new_tile_model):
        self.manager.add_tile(new_tile_model)
        self.manager.save_to_file()
        current_view = self.view_switcher.get()
        columns = int(current_view[-2]) if "Siatka" in current_view else 1
        self.draw_tiles(columns=columns)

    def draw_tiles(self, columns=1):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for i in range(10):
            self.scrollable_frame.grid_columnconfigure(i, weight=0)

        for i in range(columns):
            self.scrollable_frame.grid_columnconfigure(i, weight=1)

        # ZAAWANSOWANE SORTOWANIE:
        # 1. x.is_completed (False ląduje przed True, więc zrobione spadają na dół)
        # 2. st.PRIORITY_RANK (sortuje według przypisanych "wag" 1-5, od najważniejszych do najmniej ważnych)
        sorted_tiles = sorted(
            self.manager.tiles,
            key=lambda x: (x.is_completed, st.PRIORITY_RANK.get(x.priority, 5))
        )

        for index, tile_model in enumerate(sorted_tiles):
            wiersz = index // columns
            kolumna = index % columns

            tile_widget = ProjectTileWidget(
                master=self.scrollable_frame,
                tile_model=tile_model,
                save_callback=self.manager.save_to_file,
                delete_callback=self.delete_tile,
                complete_callback=self.complete_tile,
                edit_callback=self.edit_tile,
                restore_callback=self.restore_tile  # <--- Przekazujemy nową funkcję
            )
            tile_widget.grid(row=wiersz, column=kolumna, padx=10, pady=10, sticky="nsew")

    def restore_tile(self, tile_model):
        """Przywraca kafelek do aktywnych projektów i odświeża widok"""
        tile_model.is_completed = False
        self.manager.save_to_file()
        current_view = self.view_switcher.get()
        columns = int(current_view[-2]) if "Siatka" in current_view else 1
        self.draw_tiles(columns=columns)

    def delete_tile(self, tile_model):
        self.manager.tiles.remove(tile_model)
        self.manager.save_to_file()
        current_view = self.view_switcher.get()
        columns = int(current_view[-2]) if "Siatka" in current_view else 1
        self.draw_tiles(columns=columns)

    def complete_tile(self, tile_model):
        tile_model.is_completed = True
        self.manager.save_to_file()
        current_view = self.view_switcher.get()
        columns = int(current_view[-2]) if "Siatka" in current_view else 1
        self.draw_tiles(columns=columns)

    def edit_tile(self, tile_model):
        dialog = TileFormDialog(master=self, on_save_callback=self.update_existing_tile, existing_tile=tile_model)

    def update_existing_tile(self, updated_model):
        self.manager.save_to_file()
        current_view = self.view_switcher.get()
        columns = int(current_view[-2]) if "Siatka" in current_view else 1
        self.draw_tiles(columns=columns)

if __name__ == "__main__":
    app = SmartProjectTilesApp()
    app.mainloop()