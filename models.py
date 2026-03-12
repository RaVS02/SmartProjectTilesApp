import uuid
import json
import os
from datetime import datetime

class ProjectTileModel:
    def __init__(self, title, tags=None, priority="low", deadline=None, color=None, content=None, is_completed=False,
                 is_pinned=False, has_workflow=False, workflow_data=None, is_archived=False, tile_id=None):
        self.id = tile_id if tile_id else str(uuid.uuid4())
        self.is_completed = is_completed
        self.is_pinned = is_pinned
        self.is_archived = is_archived # <--- NOWA FLAGA KOSZA
        self.title = title
        self.tags = tags if tags is not None else []
        self.priority = priority
        self.deadline = deadline
        self.color = color
        self.content = content if content is not None else {"text": None, "todos": []}
        self.has_workflow = has_workflow
        self.workflow_data = workflow_data if workflow_data is not None else {"nodes": [], "edges": []}

    @property
    def days_left(self):
        if not self.deadline: return None
        try:
            deadline_date = datetime.strptime(self.deadline, "%Y-%m-%d").date()
            today = datetime.now().date()
            return (deadline_date - today).days
        except ValueError:
            return None

    @property
    def total_weight(self):
        from settings import PRIORITY_RANK
        p_weight = PRIORITY_RANK.get(self.priority, 5)
        t_weight = 6
        dl = self.days_left
        if dl is not None:
            if dl < 0: t_weight = 1
            elif dl == 0: t_weight = 2
            elif dl <= 3: t_weight = 3
            elif dl <= 7: t_weight = 4
            elif dl <= 14: t_weight = 5
            else: t_weight = 6
        return p_weight + t_weight

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "is_completed": self.is_completed,
            "is_pinned": self.is_pinned,
            "is_archived": self.is_archived, # Zapisywanie
            "has_workflow": self.has_workflow,
            "workflow_data": self.workflow_data,
            "tags": self.tags,
            "priority": self.priority,
            "deadline": self.deadline,
            "color": self.color,
            "content": self.content
        }

class TileManager:
    def __init__(self, filepath="data.json"):
        self.filepath = filepath
        self.tiles = []
        self.preferences = {}

    def add_tile(self, tile_model):
        self.tiles.append(tile_model)

    def save_to_file(self):
        data = {
            "preferences": self.preferences,
            "project_tiles": [t.to_dict() for t in self.tiles]
        }
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_from_file(self):
        if not os.path.exists(self.filepath): return
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "preferences" in data:
                    self.preferences.update(data["preferences"])

                tiles_list = data.get("project_tiles", [])
                for tile_data in tiles_list:
                    nowy_kafelek = ProjectTileModel(
                        title=tile_data["title"],
                        tags=tile_data.get("tags", []),
                        priority=tile_data.get("priority", "low"),
                        is_completed=tile_data.get("is_completed", False),
                        is_pinned=tile_data.get("is_pinned", False),
                        is_archived=tile_data.get("is_archived", False), # Odczytywanie
                        has_workflow=tile_data.get("has_workflow", False),
                        workflow_data=tile_data.get("workflow_data", {"nodes": [], "edges": []}),
                        deadline=tile_data.get("deadline"),
                        color=tile_data.get("color"),
                        content=tile_data.get("content"),
                        tile_id=tile_data.get("id")
                    )
                    self.add_tile(nowy_kafelek)
        except Exception as e:
            print(f"Błąd wczytywania: {e}")