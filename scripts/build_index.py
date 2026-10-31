import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rag.indexer import MedicalIndexer


if __name__ == "__main__":
    count = MedicalIndexer().build()
    print(f"索引完成：{count} chunks")
