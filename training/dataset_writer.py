"""
training/dataset_writer.py — JSONL file I/O for dataset collection.

One file per session in datasets/organic/.
One JSON line per turn, flushed immediately.
Writes summary_<session_id>_<date>.json at close.
"""
import json
import os
from datetime import datetime, timezone


class DatasetWriter:
    def __init__(self, output_dir: str, session_id: str):
        os.makedirs(output_dir, exist_ok=True)
        self._output_dir = output_dir
        self._session_id = session_id
        self._date_str   = datetime.now(timezone.utc).strftime("%Y%m%d")
        data_path        = os.path.join(
            output_dir,
            f"organic_{session_id}_{self._date_str}.jsonl",
        )
        self._fh = open(data_path, "a", encoding="utf-8")

    def write(self, record: dict) -> None:
        self._fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._fh.flush()

    def close(self, summary: dict) -> None:
        self._fh.close()
        summary_path = os.path.join(
            self._output_dir,
            f"summary_{self._session_id}_{self._date_str}.json",
        )
        with open(summary_path, "w", encoding="utf-8") as sf:
            json.dump(summary, sf, indent=2, ensure_ascii=False)
