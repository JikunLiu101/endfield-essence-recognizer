from typing import Any, Self

from pydantic import BaseModel


class TableCfg(BaseModel):
    wiki_entry_data_table: Any
    wiki_entry_table: Any
    wiki_group_table: Any


class EndfieldData(BaseModel):
    table_cfg: TableCfg

    @classmethod
    def load(cls) -> Self:
        import importlib.resources
        import json

        with importlib.resources.as_file(
            importlib.resources.files("endfield_essence_recognizer")
            / "data/endfield_game_data.json"
        ) as file_path:
            obj = json.loads(file_path.read_text(encoding="utf-8"))
            return cls.model_validate(obj)
