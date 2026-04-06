from __future__ import annotations

import json
import sys

from tqdm import tqdm

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import FINAL_DATASET_DIR, FIXED_DATA_DIR, PREPROCESSED_DATA_DIR, ensure_stage04_runtime_dirs


def prepare_final_dataset() -> None:
    source_data_dir = PREPROCESSED_DATA_DIR
    annotation_data_dir = FIXED_DATA_DIR
    ready_data_dir = FINAL_DATASET_DIR

    ensure_stage04_runtime_dirs()

    print("--- Начало подготовки финального датасета ---")

    if not source_data_dir.exists() or not annotation_data_dir.exists():
        print(f"❌ Ошибка: Не найдены необходимые директории: '{source_data_dir}' или '{annotation_data_dir}'.")
        print("Пожалуйста, сначала запустите 01_preprocessor/main.py и один из entrypoint'ов 03_generation.")
        return

    print(f"Финальный датасет будет сохранен в: '{ready_data_dir}'")

    for annotation_filepath in annotation_data_dir.glob("*.jsonl"):
        split_name = annotation_filepath.stem
        source_filepath = source_data_dir / f"{split_name}.json"
        output_filepath = ready_data_dir / f"{split_name}.json"

        print(f"\n--- Обработка набора: '{split_name}' ---")
        if not source_filepath.exists():
            print(f"  - ⚠️  Пропуск: Не найден исходный файл {source_filepath}")
            continue

        print(f"  - Загрузка исходных данных из {source_filepath.name}...")
        try:
            with open(source_filepath, "r", encoding="utf-8") as f:
                source_data = json.load(f)
            source_map = {item["sentence_id"]: item for item in source_data if isinstance(item, dict) and item.get("sentence_id")}
        except (json.JSONDecodeError, IOError) as e:
            print(f"  - ❌ Ошибка при чтении исходного файла: {e}")
            continue

        final_records = []
        print(f"  - Обработка размеченных данных из {annotation_filepath.name}...")
        try:
            with open(annotation_filepath, "r", encoding="utf-8") as f:
                for line in tqdm(f, desc=f"  - {split_name}"):
                    try:
                        annotation_record = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    sentence_id = annotation_record.get("sentence_id")
                    source_record = source_map.get(sentence_id)
                    if not source_record:
                        continue

                    annotated_nodes = annotation_record.get("nodes", [])
                    source_nodes = source_record.get("nodes", [])
                    if len(annotated_nodes) != len(source_nodes):
                        print(
                            f"  - ⚠️  Пропуск sentence_id={sentence_id}: "
                            f"кол-во узлов не совпадает "
                            f"(annotation={len(annotated_nodes)} source={len(source_nodes)})."
                        )
                        continue

                    annotated_ids = {node.get("id") for node in annotated_nodes}
                    source_ids = {node.get("id") for node in source_nodes}
                    if annotated_ids != source_ids:
                        print(f"  - ⚠️  Пропуск sentence_id={sentence_id}: id узлов не совпадают.")
                        continue

                    annotated_nodes_map = {node["id"]: node for node in annotated_nodes if isinstance(node, dict) and node.get("id")}
                    transformed_nodes = []
                    for source_node in source_nodes:
                        node_id = source_node["id"]
                        annotated_node = annotated_nodes_map.get(node_id)
                        if not annotated_node:
                            continue

                        transformed_nodes.append(
                            {
                                "id": node_id,
                                "name": source_node.get("name"),
                                "pos_universal": source_node.get("pos_universal"),
                                "case": source_node.get("features", {}).get("Case"),
                                "syntactic_link_name": annotated_node.get("syntactic_link_name"),
                                "syntactic_link_target_id": source_node.get("syntactic_link_target_id"),
                            }
                        )

                    final_records.append({"input": source_record.get("text"), "output": transformed_nodes})

            print(f"  - Найдено и обработано {len(final_records)} записей.")
            print(f"  - Сохранение в {output_filepath}...")
            with open(output_filepath, "w", encoding="utf-8") as f:
                json.dump(final_records, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"  - ❌ Ошибка при чтении размеченного файла: {e}")
            continue

    print("\n--- ✅ Подготовка финального датасета успешно завершена! ---")


if __name__ == "__main__":
    prepare_final_dataset()
