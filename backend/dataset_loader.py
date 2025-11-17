"""Dataset loader utilities for prompt-HTML pairs."""

import os
from threading import Lock
from typing import Dict, List, Optional

import pyarrow as pa
import pyarrow.ipc as ipc

from config import Config


class DatasetLoaderError(Exception):
    """Custom exception for dataset loader issues."""


class DatasetLoader:
    """Load and serve dataset samples from Arrow file."""

    _instance = None
    _lock: Lock = Lock()

    def __init__(self, arrow_path: str):
        self.arrow_path = arrow_path
        self._table: Optional[pa.Table] = None
        self._load_dataset()

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(Config.DATASET_ARROW_FILE)
            return cls._instance

    def _load_dataset(self):
        if not os.path.exists(self.arrow_path):
            raise DatasetLoaderError(f"未找到数据集文件: {self.arrow_path}")

        try:
            with pa.memory_map(self.arrow_path, 'r') as source:
                self._table = self._read_table(source)
        except Exception as exc:  # pylint: disable=broad-except
            raise DatasetLoaderError(f"加载数据集失败: {str(exc)}") from exc

    @staticmethod
    def _read_table(source: pa.NativeFile) -> pa.Table:
        """Read Arrow data supporting both file and stream formats."""
        try:
            reader = ipc.RecordBatchFileReader(source)
            return reader.read_all()
        except pa.ArrowInvalid:
            source.seek(0)
            stream_reader = ipc.RecordBatchStreamReader(source)
            return stream_reader.read_all()

    @property
    def ready(self) -> bool:
        return self._table is not None

    @property
    def size(self) -> int:
        if not self._table:
            return 0
        return self._table.num_rows

    def list_samples(self, offset: int = 0, limit: int = 20) -> Dict[str, object]:
        if not self.ready:
            raise DatasetLoaderError("数据集尚未加载")

        offset = max(offset, 0)
        limit = max(min(limit, 100), 1)
        total = self.size

        if offset >= total:
            return {
                'samples': [],
                'total': total,
                'matched': 0
            }

        slice_size = min(limit, total - offset)
        sliced = self._table.slice(offset, slice_size)

        samples: List[Dict[str, object]] = []
        columns = sliced.to_pydict()

        for idx in range(slice_size):
            samples.append({
                'id': offset + idx,
                'prompt': columns.get('prompt', [''])[idx],
                'prompt_type': columns.get('prompt_type', [''])[idx],
                'dataset_source': columns.get('dataset_source', [''])[idx]
            })

        return {
            'samples': samples,
            'total': total,
            'matched': slice_size
        }

    def search_samples(self, query: str, limit: int = 50) -> Dict[str, object]:
        if not self.ready:
            raise DatasetLoaderError("数据集尚未加载")

        if not query:
            return self.list_samples(limit=limit)

        limit = max(min(limit, 100), 1)
        normalized = query.lower()

        data = self._table.to_pydict()
        prompts = data.get('prompt', [])
        prompt_types = data.get('prompt_type', [])
        sources = data.get('dataset_source', [])

        samples: List[Dict[str, object]] = []
        matched_count = 0

        for idx, prompt in enumerate(prompts):
            prompt_text = prompt or ''
            if normalized in prompt_text.lower():
                matched_count += 1
                if len(samples) < limit:
                    samples.append({
                        'id': idx,
                        'prompt': prompt_text,
                        'prompt_type': prompt_types[idx] if idx < len(prompt_types) else '',
                        'dataset_source': sources[idx] if idx < len(sources) else ''
                    })

        return {
            'samples': samples,
            'total': self.size,
            'matched': matched_count
        }

    def get_sample(self, sample_id: int) -> Dict[str, object]:
        if not self.ready:
            raise DatasetLoaderError("数据集尚未加载")

        if sample_id < 0 or sample_id >= self.size:
            raise DatasetLoaderError("样本 ID 超出范围")

        row = self._table.slice(sample_id, 1).to_pydict()
        return {
            'id': sample_id,
            'prompt': row.get('prompt', [''])[0],
            'html': row.get('html', [''])[0],
            'prompt_type': row.get('prompt_type', [''])[0],
            'dataset_source': row.get('dataset_source', [''])[0],
            'original_index': row.get('original_index', [sample_id])[0]
        }


def get_dataset_loader() -> DatasetLoader:
    """Helper to get singleton dataset loader."""
    return DatasetLoader.get_instance()
