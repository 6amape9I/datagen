from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pyconll


def detect_split_from_filename(filename: str) -> Optional[str]:
    lowered = filename.lower()
    if "train" in lowered:
        return "train"
    if "dev" in lowered or "val" in lowered:
        return "val"
    if "test" in lowered:
        return "test"
    return None


def discover_language_configs(raw_corpus_dir: Path) -> Dict[str, Dict[str, List[Path]]]:
    language_configs: Dict[str, Dict[str, List[Path]]] = {}

    if not raw_corpus_dir.exists():
        return language_configs

    for language_dir in sorted(path for path in raw_corpus_dir.iterdir() if path.is_dir()):
        file_mappings: Dict[str, List[Path]] = {"train": [], "val": [], "test": []}
        for conllu_path in sorted(language_dir.rglob("*.conllu")):
            split_name = detect_split_from_filename(conllu_path.name)
            if not split_name:
                print(f"⚠️  Пропуск {conllu_path}: не удалось определить split (train/dev/test).")
                continue
            file_mappings[split_name].append(conllu_path)

        if any(file_mappings.values()):
            language_configs[language_dir.name] = file_mappings

    return language_configs


def load_corpus(filepath: Path) -> pyconll.unit.conll.Conll:
    return pyconll.load_from_file(str(filepath))


def iter_sentences(
    filepath: Path,
    *,
    sentence_limit: Optional[int] = None,
) -> Iterable[tuple[int, pyconll.unit.sentence.Sentence]]:
    corpus = load_corpus(filepath)
    for sent_idx, sentence in enumerate(corpus):
        if sentence_limit is not None and sent_idx >= sentence_limit:
            break
        yield sent_idx, sentence
