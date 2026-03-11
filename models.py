import uuid
import json
import os

class ProjectTileModel:
    def __init__(self, title, tags=None, priority="low", deadline=None, color=None, content=None,is_completed=False, tile_id=None):
        # 1. Identyfikator:
        # Jeśli wczytujemy kafelek z JSON-a, podamy jego istniejące ID.
        # Jeśli tworzymy nowy, Python sam wygeneruje mu unikalny ciąg znaków (UUID).
        self.id = tile_id if tile_id else str(uuid.uuid4())
        self.is_completed = is_completed

        self.title = title

        # Ważne: Jeśli argument 'tags' ma wartość None (nic nie podano), przypisz do self.tags pustą listę: []
        if tags is not None:
            self.tags = tags  # Zapisujemy tagi podane przez użytkownika
        else:
            self.tags = []  # Użytkownik nic nie podał, tworzymy pustą listę


        self.priority=priority

        self.deadline=deadline

        self.color=color
        # 2. Zawartość (Content):

        if content is not None:
            self.content=content
        else:
            self.content={"text": None, "todos": []}

        # Jeśli jest None, stwórz i przypisz domyślny słownik o strukturze zgodnej z naszym JSON-em:
        # klucz "text" ustawiony na None oraz klucz "todos" ustawiony na pustą listę [].

    def __repr__(self):
        """To mała funkcja pomocnicza. Dzięki niej, gdy zrobisz print(twoj_kafelek),
        zobaczysz ładny napis zamiast technicznego bełkotu."""
        return f"<ProjectTileModel: '{self.title}' (Priorytet: {self.priority})>"

    def to_dict(self):
        """
        Przekształca obiekt kafelka na słownik, gotowy do zapisu w pliku JSON.
        Struktura musi idealnie pasować do tego, co zaplanowaliśmy w Etapie 1.
        """
        return {
            "id": self.id,
            "title": self.title,
            "is_completed": self.is_completed,
            "tags": self.tags,
            "priority": self.priority,
            "deadline": self.deadline,
            "color": self.color,
            "content":self.content
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
        """Wczytuje kafelki z pliku JSON do pamięci (do listy self.tiles)"""
        # 1. Czyścimy obecną listę, żeby nie dublować kafelków przy ponownym wczytaniu
        self.tiles = []

        try:
            with open(self.filepath, "r", encoding="utf-8") as file:
                # Wczytujemy cały plik JSON do zmiennej jako słownik
                data = json.load(file)

                # Wyciągamy samą listę kafelków
                tiles_list = data.get("project_tiles", [])

                # 2. Odtwarzamy obiekty z danych
                for tile_data in tiles_list:
                    # TODO: Stwórz nowy obiekt ProjectTileModel.

                    # Musisz wyciągnąć dane z 'tile_data' (które jest słownikiem)
                    # i przekazać je do konstruktora.
                    # Podpowiedź: tile_data["title"], tile_data["priority"] itd.
                    # PAMIĘTAJ o przekazaniu ID, żeby kafelek zachował swój stary identyfikator!
                    nowy_kafelek = ProjectTileModel(
                        title=tile_data["title"],
                        tags=tile_data["tags"],
                        priority=tile_data["priority"],
                        is_completed=tile_data.get("is_completed", False),
                        deadline=tile_data["deadline"],
                        color=tile_data["color"],
                        content=tile_data["content"],
                        tile_id=tile_data["id"]
                    )
                    self.add_tile(nowy_kafelek)
                    # TODO: Dodaj 'nowy_kafelek' do menedżera używając metody self.add_tile()

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