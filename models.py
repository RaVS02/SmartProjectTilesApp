import uuid
import json
import os
from datetime import datetime # <--- NOWY IMPORT

class ProjectTileModel:
    # Dodano is_pinned=False
    def __init__(self, title, tags=None, priority="low", deadline=None, color=None, content=None, is_completed=False, is_pinned=False, tile_id=None):
        self.id = tile_id if tile_id else str(uuid.uuid4())
        self.is_completed = is_completed
        self.is_pinned = is_pinned # <--- NOWE
        self.title = title
        self.tags = tags if tags is not None else []
        self.priority = priority
        self.deadline = deadline
        self.color = color
        self.content = content if content is not None else {"text": None, "todos": []}

    @property
    def days_left(self):
        if not self.deadline: return None
        try:
            deadline_date = datetime.strptime(self.deadline, "%Y-%m-%d").date()
            today = datetime.now().date()
            return (deadline_date - today).days
        except ValueError: return None

    @property
    def time_weight(self):
        dl = self.days_left
        if dl is None: return 6
        if dl < 0: return 1
        if dl == 0: return 1
        if dl <= 3: return 2
        if dl <= 7: return 3
        if dl <= 14: return 4
        return 5

    @property
    def total_weight(self):
        from settings import PRIORITY_RANK
        p_weight = PRIORITY_RANK.get(self.priority, 5)
        return p_weight + self.time_weight

    def __repr__(self):
        return f"<ProjectTileModel: '{self.title}' (Priorytet: {self.priority}, Deadline: {self.deadline})>"

    def to_dict(self):
        # Dodano zapis is_pinned
        return {
            "id": self.id, "title": self.title, "is_completed": self.is_completed, "is_pinned": self.is_pinned,
            "tags": self.tags, "priority": self.priority, "deadline": self.deadline, "color": self.color, "content": self.content
        }

class TileManager:
    def __init__(self, filepath="data.json"):
        self.filepath = filepath
        self.tiles = []  # Tu będziemy trzymać obiekty ProjectTileModel

    def add_tile(self, tile):
        """Dodaje nowy kafelek do listy w pamięci"""
        self.tiles.append(tile)

    def save_to_file(self):
        """Zapisuje obecny stan kafelków do pliku JSON"""

        tiles_data = []

        for tile in self.tiles:
            tiles_data.append(tile.to_dict())

        final_data = {"project_tiles": tiles_data}


        # 3. Zapis do pliku (ten fragment daję gotowy, bo operacje I/O bywają kapryśne)
        # Używamy bloku 'with', który automatycznie zamknie plik po zakończeniu zapisu
        try:
            with open(self.filepath, "w", encoding="utf-8") as file:
                json.dump(final_data, file, indent=4, ensure_ascii=False)
            print(f"Pomyślnie zapisano dane do {self.filepath}")
        except Exception as e:
            print(f"Błąd podczas zapisu do pliku: {e}")

    def load_from_file(self):
        self.tiles = []
        try:
            with open(self.filepath, "r", encoding="utf-8") as file:
                data = json.load(file)
                tiles_list = data.get("project_tiles", [])

                for tile_data in tiles_list:
                    nowy_kafelek = ProjectTileModel(
                        title=tile_data["title"],
                        tags=tile_data["tags"],
                        priority=tile_data["priority"],
                        is_completed=tile_data.get("is_completed", False),
                        is_pinned=tile_data.get("is_pinned", False),  # <--- NOWE Odczytywanie
                        deadline=tile_data["deadline"],
                        color=tile_data["color"],
                        content=tile_data["content"],
                        tile_id=tile_data["id"]
                    )
                    self.add_tile(nowy_kafelek)
            print(f"Pomyślnie wczytano dane z {self.filepath}")
        except FileNotFoundError:
            print(f"Plik {self.filepath} nie istnieje. Zaczynamy z czystą kartą.")
        except Exception as e:
            print(f"Błąd podczas wczytywania pliku: {e}")

# --- TESTOWANIE BACKENDU ---
if __name__ == "__main__":
    manager = TileManager()
    manager.load_from_file()
    print("Wczytane kafelki:")
    print(manager.tiles)