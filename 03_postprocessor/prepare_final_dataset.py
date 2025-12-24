# postprocess/prepare_final_dataset.py

# Добавляем sys.path для корректного импорта 'config' из родительской директории
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import json
from tqdm import tqdm

# --- 1. Импортируем пути из централизованного конфига ---
from config.paths import PREPROCESSED_DATA_DIR, GENERATED_DATA_DIR, FINAL_DATASET_DIR


def prepare_final_dataset():
    """
    Скрипт для создания финального, чистого датасета.
    Объединяет данные из '02_preprocessed' и '03_generated',
    преобразует их в формат input/output и сохраняет в '04_final'.
    """
    # --- Пути теперь берутся из config ---
    SOURCE_DATA_DIR = PREPROCESSED_DATA_DIR
    BATTLE_DATA_DIR = GENERATED_DATA_DIR
    READY_DATA_DIR = FINAL_DATASET_DIR

    print("--- Начало подготовки финального датасета ---")

    if not SOURCE_DATA_DIR.exists() or not BATTLE_DATA_DIR.exists():
        print(f"❌ Ошибка: Не найдены необходимые директории: '{SOURCE_DATA_DIR}' или '{BATTLE_DATA_DIR}'.")
        print("Пожалуйста, сначала запустите preprocessor/main.py и gemini_generate/pipeline.py.")
        return

    print(f"Финальный датасет будет сохранен в: '{READY_DATA_DIR}'")

    # --- 2. Обработка каждого набора данных (train, val, test) ---
    for battle_filepath in BATTLE_DATA_DIR.glob("*.jsonl"):
        split_name = battle_filepath.stem
        source_filepath = SOURCE_DATA_DIR / f"{split_name}.json"
        output_filepath = READY_DATA_DIR / f"{split_name}.json"

        # ... (остальной код функции остается без изменений) ...
        # ... (он уже был написан хорошо, нужно было только заменить пути) ...

        print(f"\n--- Обработка набора: '{split_name}' ---")
        if not source_filepath.exists():
            print(f"  - ⚠️  Пропуск: Не найден исходный файл {source_filepath}")
            continue
        print(f"  - Загрузка исходных данных из {source_filepath.name}...")
        try:
            with open(source_filepath, 'r', encoding='utf-8') as f:
                source_data = json.load(f)
            source_map = {item['sentence_id']: item for item in source_data}
        except (json.JSONDecodeError, IOError) as e:
            print(f"  - ❌ Ошибка при чтении исходного файла: {e}")
            continue
        final_records = []
        print(f"  - Обработка размеченных данных из {battle_filepath.name}...")
        try:
            with open(battle_filepath, 'r', encoding='utf-8') as f:
                for line in tqdm(f, desc=f"  - {split_name}"):
                    try:
                        battle_record = json.loads(line)
                        sentence_id = battle_record.get("sentence_id")
                        source_record = source_map.get(sentence_id)
                        if not source_record: continue
                        annotated_nodes_map = {node['id']: node for node in battle_record['nodes']}
                        transformed_nodes = []
                        for source_node in source_record['nodes']:
                            node_id = source_node['id']
                            annotated_node = annotated_nodes_map.get(node_id)
                            if not annotated_node: continue
                            case_value = source_node.get('features', {}).get('Case')
                            new_node = {
                                "id": source_node.get('id'), "name": source_node.get('name'),
                                "pos_universal": source_node.get('pos_universal'),
                                "case": case_value,
                                "syntactic_link_name": annotated_node.get('syntactic_link_name'),
                                "syntactic_link_target_id": source_node.get('syntactic_link_target_id')
                            }
                            transformed_nodes.append(new_node)
                        final_record = {"input": source_record.get('text'), "output": transformed_nodes}
                        final_records.append(final_record)
                    except json.JSONDecodeError:
                        continue
            print(f"  - Найдено и обработано {len(final_records)} записей.")
            print(f"  - Сохранение в {output_filepath}...")
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(final_records, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"  - ❌ Ошибка при чтении размеченного файла: {e}")
            continue

    print("\n--- ✅ Подготовка финального датасета успешно завершена! ---")


if __name__ == "__main__":
    prepare_final_dataset()
