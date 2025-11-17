# preprocessor/main.py
import logging
from processor import process_syntagrus_file, get_and_reset_fallback_any_count
from utils.data_utils import save_data_to_json
from config import RAW_CORPUS_DIR, PREPROCESSED_DATA_DIR

if __name__ == "__main__":

    file_mappings = {
        "train": [
            "ru_syntagrus-ud-train-a.conllu",
            "ru_syntagrus-ud-train-b.conllu",
            "ru_syntagrus-ud-train-c.conllu",
        ],
        "val": ["ru_syntagrus-ud-dev.conllu"],
        "test": ["ru_syntagrus-ud-test.conllu"],
    }

    print("--- Начало обработки датасета SynTagRus ---")

    for split_name, filenames in file_mappings.items():
        print(f"\n--- Обработка набора '{split_name}' ---")
        all_split_data = []

        for filename in filenames:

            target_file_path = RAW_CORPUS_DIR / filename

            if not target_file_path.exists():
                print(f"❌ Ошибка: Файл не найден по пути: {target_file_path}")
                continue

            processed_data = process_syntagrus_file(target_file_path, source_filename=filename)

            if processed_data:
                all_split_data.extend(processed_data)

        output_filepath = PREPROCESSED_DATA_DIR / f"{split_name}.json"
        save_data_to_json(all_split_data, output_filepath)
        fallback_any_count = get_and_reset_fallback_any_count()
        print(f"  - ANY-fallback сработал: {fallback_any_count} раз(а) в наборе '{split_name}'.")
        try:
            logging.warning(f"FALLBACK_ANY_SUMMARY: split='{split_name}', count={fallback_any_count}")
        except Exception:
            pass

    print("\n--- ✅ Обработка всех наборов успешно завершена! ---")
