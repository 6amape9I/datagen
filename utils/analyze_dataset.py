from __future__ import annotations

import json
import pprint
from collections import defaultdict

from config import PREPROCESSED_DATA_DIR


def analyze_dataset_features() -> None:
    source_data_dir = PREPROCESSED_DATA_DIR

    if not source_data_dir.exists():
        print(f"❌ Ошибка: Директория '{source_data_dir}' не найдена.")
        print("Пожалуйста, сначала запустите 01_preprocessor/main.py, чтобы сгенерировать датасет.")
        return

    analytics = defaultdict(set)

    print(f"--- Анализ файлов в директории: {source_data_dir} ---")

    json_files = list(source_data_dir.glob("*.json"))
    if not json_files:
        print("В директории не найдены .json файлы для анализа.")
        return

    for filepath in json_files:
        print(f"  - Обработка файла: {filepath.name}...")
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            for sentence in data:
                for node in sentence.get("nodes", []):
                    if node.get("original_deprel"):
                        analytics["original_deprel"].add(node["original_deprel"])
                    if node.get("pos_universal"):
                        analytics["pos_universal"].add(node["pos_universal"])

                    features = node.get("features", {})
                    if features:
                        for feature_name, feature_value in features.items():
                            analytics[f"feature_{feature_name}"].add(feature_value)

                    for marker in node.get("introduced_by", []):
                        analytics["marker_word"].add(str(marker).lower())

    print("\n--- Результаты анализа ---")
    sorted_analytics = {key: sorted(list(value)) for key, value in analytics.items()}
    pprint.pprint(sorted_analytics)
    print("\n--- Анализ завершен ---")


if __name__ == "__main__":
    analyze_dataset_features()
