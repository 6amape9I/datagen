# Stage 03 — Generation Compatibility Notes

The canonical generation layer now lives in [`03_generation`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_generation).

`03_annotation/` remains only for compatibility wrappers:

- `pipeline.py` redirects to `03_generation/google_gen.py`
- `scheduler.py` redirects to `03_generation/scheduler.py`
- helper modules re-export prompt/schema/validator/provider symbols from `03_generation`

## Canonical commands

```bash
python 03_generation/local_gen.py
python 03_generation/google_gen.py
python 03_generation/scheduler.py
```
