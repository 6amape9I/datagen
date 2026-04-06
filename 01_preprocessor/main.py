from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import PREPROCESSED_DATA_DIR, RAW_CORPUS_DIR, ensure_stage01_runtime_dirs
from processor import process_syntagrus_file
from reader import discover_language_configs
from utils.data_utils import save_data_to_json


if __name__ == "__main__":
    ensure_stage01_runtime_dirs()

    language_configs = discover_language_configs(RAW_CORPUS_DIR)
    if not language_configs:
        print(f"❌ В {RAW_CORPUS_DIR} не найдено ни одного .conllu-файла.")
        raise SystemExit(1)

    print("--- Начало обработки датасетов ---")

    for language_code, file_mappings in language_configs.items():
        raw_dir = RAW_CORPUS_DIR / language_code
        print(f"\n--- Язык: {language_code} ---")

        for split_name in ("train", "val", "test"):
            source_files = file_mappings.get(split_name, [])
            print(f"\n--- Обработка набора '{split_name}' ---")

            if not source_files:
                print(f"⚠️  Для языка '{language_code}' не найдено .conllu файлов для split '{split_name}'.")

            all_split_data = []
            for target_file_path in source_files:
                rel_name = str(target_file_path.relative_to(raw_dir)).replace("\\", "/").replace("/", "__")
                source_filename = f"{language_code}_{rel_name}"
                processed_data = process_syntagrus_file(
                    target_file_path,
                    source_filename=source_filename,
                    language_code=language_code,
                    split_name=split_name,
                )
                if processed_data:
                    all_split_data.extend(processed_data)

            output_filepath = PREPROCESSED_DATA_DIR / f"{language_code}_{split_name}.json"
            save_data_to_json(all_split_data, output_filepath)

    print("\n--- ✅ Обработка всех наборов успешно завершена! ---")
