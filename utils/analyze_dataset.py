import json
from collections import defaultdict
import pprint

from config import PREPROCESSED_DATA_DIR
from utils.preprocessed_utils import get_legacy_nodes


def analyze_dataset_features():
    """
    Собирает статистику по уникальным значениям ключевых полей
    в датасете для построения точных эвристик.
    """
    SOURCE_DATA_DIR = PREPROCESSED_DATA_DIR

    if not SOURCE_DATA_DIR.exists():
        print(f"❌ Ошибка: Директория '{SOURCE_DATA_DIR}' не найдена.")
        print("Пожалуйста, сначала запустите 01_preprocessor/main.py, чтобы сгенерировать датасет.")
        return

    # Используем defaultdict(set) для автоматического сбора уникальных значений
    analytics = defaultdict(set)

    print(f"--- Анализ файлов в директории: {SOURCE_DATA_DIR} ---")

    json_files = list(SOURCE_DATA_DIR.glob("*.json"))
    if not json_files:
        print("В директории не найдены .json файлы для анализа.")
        return

    for filepath in json_files:
        print(f"  - Обработка файла: {filepath.name}...")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for sentence in data:
                for node in get_legacy_nodes(sentence):
                    # 1. Синтаксическая связь
                    if node.get("original_deprel"):
                        analytics["original_deprel"].add(node["original_deprel"])

                    # 2. Часть речи
                    if node.get("pos_universal"):
                        analytics["pos_universal"].add(node["pos_universal"])

                    # 3. Грамматические признаки (features)
                    features = node.get("features", {})
                    if features:
                        for feature_name, feature_value in features.items():
                            analytics[f"feature_{feature_name}"].add(feature_value)

                    # 4. Маркеры (предлоги, союзы)
                    link_info = node.get("link_introduction_info")
                    if link_info and link_info.get("marker_word"):
                        analytics["marker_word"].add(link_info["marker_word"].lower())

    print("\n--- Результаты анализа ---")
    # Преобразуем множества в отсортированные списки для красивого вывода
    sorted_analytics = {key: sorted(list(value)) for key, value in analytics.items()}
    pprint.pprint(sorted_analytics)
    print("\n--- Анализ завершен ---")


if __name__ == "__main__":
    analyze_dataset_features()
