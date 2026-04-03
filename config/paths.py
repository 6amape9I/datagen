# config/paths.py
from pathlib import Path

# Корень проекта
PROJECT_ROOT = Path(__file__).parent.parent

# --- ОБЩАЯ ПАПКА ДЛЯ ДАННЫХ ---
DATASETS_ROOT = PROJECT_ROOT / "datasets"

# --- Директории этапов обработки данных ---
RAW_CORPUS_DIR = DATASETS_ROOT / "01_raw_corpus"           # Исходные корпуса
RAW_CORPUS_RUS_DIR = RAW_CORPUS_DIR / "rus"
RAW_CORPUS_ENG_DIR = RAW_CORPUS_DIR / "eng"
PREPROCESSED_DATA_DIR = DATASETS_ROOT / "02_preprocessed"  # Выход preprocessor'а

# Новый пайплайн:
# 02_local_generation -> datasets/03_local_generated
# 03_gemini_fix_errors -> datasets/04_fixed
# 04_postprocessor -> datasets/05_final
LOCAL_GENERATED_DATA_DIR = DATASETS_ROOT / "03_local_generated"
FIXED_DATA_DIR = DATASETS_ROOT / "04_fixed"
FINAL_DATASET_DIR = DATASETS_ROOT / "05_final"

# Обратная совместимость со старым именованием.
# GENERATED_DATA_DIR ранее указывал на datasets/03_generated.
# Теперь он алиас на локальную генерацию, чтобы старые импорты не падали.
GENERATED_DATA_DIR = LOCAL_GENERATED_DATA_DIR

# --- Директории служебных файлов ---
LOGS_DIR = PROJECT_ROOT / "logs"
UTILS_DIR = PROJECT_ROOT / "utils"

# --- Файлы логов ---
PROCESSOR_LOG_PATH = LOGS_DIR / "processor_fallback.log"
VALIDATOR_LOG_PATH = LOGS_DIR / "validator_errors.log"
SCHEDULER_LOG_PATH = LOGS_DIR / "scheduler_summary.log"
LOCAL_GENERATION_LOG_PATH = LOGS_DIR / "local_generation_errors.log"

# --- Создаем необходимые директории при старте ---
DATASETS_ROOT.mkdir(exist_ok=True)
RAW_CORPUS_DIR.mkdir(exist_ok=True)
RAW_CORPUS_RUS_DIR.mkdir(exist_ok=True)
RAW_CORPUS_ENG_DIR.mkdir(exist_ok=True)
PREPROCESSED_DATA_DIR.mkdir(exist_ok=True)
LOCAL_GENERATED_DATA_DIR.mkdir(exist_ok=True)
FIXED_DATA_DIR.mkdir(exist_ok=True)
FINAL_DATASET_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
UTILS_DIR.mkdir(exist_ok=True)
