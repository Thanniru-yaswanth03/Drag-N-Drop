import json
from pathlib import Path
from jsonschema import validate

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR.parent / "docs" / "schema.json"

def test_schema_json_validity():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    assert schema["title"] == "KanbanBoardSchema"

def test_initial_data_conforms_to_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)

    sample_board = {
        "boardId": "col-board-1",
        "userId": "user-1",
        "columns": [
            {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"]},
            {"id": "col-discovery", "title": "Discovery", "cardIds": ["card-3"]},
            {"id": "col-progress", "title": "In Progress", "cardIds": ["card-4"]},
            {"id": "col-review", "title": "Review", "cardIds": []},
            {"id": "col-done", "title": "Done", "cardIds": []},
        ],
        "cards": {
            "card-1": {
                "id": "card-1",
                "title": "Align roadmap themes",
                "details": "Draft quarterly themes.",
            },
            "card-2": {
                "id": "card-2",
                "title": "Gather customer signals",
                "details": "Review support tags.",
            },
            "card-3": {
                "id": "card-3",
                "title": "Prototype analytics view",
                "details": "Sketch dashboard layout.",
            },
            "card-4": {
                "id": "card-4",
                "title": "Refine status language",
                "details": "Standardize labels.",
            },
        },
    }

    # Should not raise jsonschema.exceptions.ValidationError
    validate(instance=sample_board, schema=schema)
