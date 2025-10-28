"""Histogram storage using Lance (grouped by namespace)

Strategy:
1. One Lance file per namespace:
   - params/layer1, params/layer2 → params_i32.lance (if int32)
   - gradients/layer1, gradients/layer2 → gradients_i32.lance
   - custom → custom_i32.lance
2. Precision is per-file (suffix: _u8 or _i32)
3. Schema includes "name" field (full name with namespace)

Schema:
- step: int64
- global_step: int64
- name: string (full name: "params/layer1")
- counts: list<uint8 or int32>
- min: float32 (p1)
- max: float32 (p99)
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pyarrow as pa
from lance.dataset import write_dataset
from loguru import logger


class HistogramStorage:
    """Histogram storage with namespace-based grouping"""

    def __init__(self, base_dir: Path, num_bins: int = 64):
        """Initialize histogram storage

        Args:
            base_dir: Base directory
            num_bins: Number of bins (default: 64)
        """
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.histograms_dir = base_dir / "histograms"
        self.histograms_dir.mkdir(exist_ok=True)

        self.num_bins = num_bins

        # Buffers grouped by namespace + precision
        # Key: "{namespace}_{u8|i32}"
        self.buffers: Dict[str, List[Dict[str, Any]]] = {}

        # Schemas
        self.schema_uint8 = pa.schema(
            [
                pa.field("step", pa.int64()),
                pa.field("global_step", pa.int64()),
                pa.field("name", pa.string()),
                pa.field("counts", pa.list_(pa.uint8())),
                pa.field("min", pa.float32()),
                pa.field("max", pa.float32()),
            ]
        )

        self.schema_int32 = pa.schema(
            [
                pa.field("step", pa.int64()),
                pa.field("global_step", pa.int64()),
                pa.field("name", pa.string()),
                pa.field("counts", pa.list_(pa.int32())),
                pa.field("min", pa.float32()),
                pa.field("max", pa.float32()),
            ]
        )

    def append_histogram(
        self,
        step: int,
        global_step: Optional[int],
        name: str,
        values: List[float],
        num_bins: int = None,
        precision: str = "exact",
    ):
        """Append histogram

        Args:
            step: Step number
            global_step: Global step
            name: Histogram name (e.g., "gradients/layer1")
            values: Raw values
            num_bins: Ignored
            precision: "exact" (int32, default) or "compact" (uint8)
        """
        if not values:
            return

        values_array = np.array(values, dtype=np.float32)
        values_array = values_array[np.isfinite(values_array)]

        if len(values_array) == 0:
            return

        # Compute p1-p99 range
        p1 = float(np.percentile(values_array, 1))
        p99 = float(np.percentile(values_array, 99))

        if p99 - p1 < 1e-6:
            p1 = float(values_array.min())
            p99 = float(values_array.max())
            if p99 - p1 < 1e-6:
                p1 -= 0.5
                p99 += 0.5

        # Compute histogram
        counts, _ = np.histogram(values_array, bins=self.num_bins, range=(p1, p99))

        # Convert based on precision
        if precision == "compact":
            max_count = counts.max()
            final_counts = (
                (counts / max_count * 255).astype(np.uint8)
                if max_count > 0
                else counts.astype(np.uint8)
            )
            schema = self.schema_uint8
            suffix = "_u8"
        else:
            final_counts = counts.astype(np.int32)
            schema = self.schema_int32
            suffix = "_i32"

        # Extract namespace
        namespace = name.split("/")[0] if "/" in name else name.replace("/", "__")
        buffer_key = f"{namespace}{suffix}"

        # Initialize buffer
        if buffer_key not in self.buffers:
            self.buffers[buffer_key] = []

        # Add to buffer
        self.buffers[buffer_key].append(
            {
                "step": step,
                "global_step": global_step,
                "name": name,
                "counts": final_counts.tolist(),
                "min": p1,
                "max": p99,
            }
        )

        # Store schema
        if not hasattr(self, "_schemas"):
            self._schemas = {}
        self._schemas[buffer_key] = schema

    def flush(self):
        """Flush all buffers (writes to ~2-4 Lance files total)"""
        if not self.buffers:
            return

        total_entries = sum(len(buf) for buf in self.buffers.values())
        total_files = len(self.buffers)

        for buffer_key, buffer in list(self.buffers.items()):
            if not buffer:
                continue

            try:
                schema = self._schemas.get(buffer_key, self.schema_int32)
                table = pa.Table.from_pylist(buffer, schema=schema)
                hist_file = self.histograms_dir / f"{buffer_key}.lance"

                if hist_file.exists():
                    write_dataset(table, str(hist_file), mode="append")
                else:
                    write_dataset(table, str(hist_file))

                buffer.clear()

            except Exception as e:
                logger.error(f"Failed to flush {buffer_key}: {e}")

        logger.debug(f"Flushed {total_entries} histograms to {total_files} Lance files")

    def close(self):
        """Close storage"""
        self.flush()
        logger.debug("Histogram storage closed")
