# preprocessor/main.py
import logging
from processor import process_syntagrus_file, get_and_reset_fallback_any_count
from utils.data_utils import save_data_to_json
from config import RAW_CORPUS_RUS_DIR, RAW_CORPUS_ENG_DIR, PREPROCESSED_DATA_DIR

if __name__ == "__main__":

    language_configs = {
        "rus": {
            "raw_dir": RAW_CORPUS_RUS_DIR,
            "file_mappings": {
                "train": [
                    "ru_syntagrus-ud-train-a.conllu",
                    "ru_syntagrus-ud-train-b.conllu",
                    "ru_syntagrus-ud-train-c.conllu",
                ],
                "val": ["ru_syntagrus-ud-dev.conllu"],
                "test": ["ru_syntagrus-ud-test.conllu"],
            },
        },
        "eng": {
            "raw_dir": RAW_CORPUS_ENG_DIR,
            "file_mappings": {
                "train": ["en_gum-ud-train.conllu"],
                "val": ["en_gum-ud-dev.conllu"],
                "test": ["en_gum-ud-test.conllu"],
            },
        },
    }

    print("--- Начало обработки датасетов ---")

    for language_code, config in language_configs.items():
        raw_dir = config["raw_dir"]
        file_mappings = config["file_mappings"]
        print(f"\n--- Язык: {language_code} ---")

        for split_name, filenames in file_mappings.items():
            print(f"\n--- Обработка набора '{split_name}' ---")
            all_split_data = []

            for filename in filenames:
                target_file_path = raw_dir / filename

                if not target_file_path.exists():
                    print(f"❌ Ошибка: Файл не найден по пути: {target_file_path}")
                    continue

                processed_data = process_syntagrus_file(
                    target_file_path,
                    source_filename=f"{language_code}_{filename}",
                )

                if processed_data:
                    all_split_data.extend(processed_data)

            output_filepath = PREPROCESSED_DATA_DIR / f"{language_code}_{split_name}.json"
            save_data_to_json(all_split_data, output_filepath)
            fallback_any_count = get_and_reset_fallback_any_count()
            print(f"  - ANY-fallback сработал: {fallback_any_count} раз(а) в наборе '{split_name}'.")
            try:
                logging.warning(
                    f"FALLBACK_ANY_SUMMARY: lang='{language_code}', split='{split_name}', count={fallback_any_count}"
                )
            except Exception:
                pass

    print("\n--- ✅ Обработка всех наборов успешно завершена! ---")
