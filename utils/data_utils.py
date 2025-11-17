# data_utils.py
import json
from pathlib import Path
from typing import List, Dict, Any


def save_data_to_json(data: List[Dict[str, Any]], output_path: Path):
    """
    Сохраняет список обработанных предложений в один JSON-файл.
    """
    if not data:
        print(f"⚠️ Предупреждение: Нет данных для сохранения в {output_path.name}.")
        return

    # Убедимся, что родительская директория существует
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Сохранен файл {output_path} ({len(data)} предложений)")