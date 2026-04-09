from __future__ import annotations

import argparse
import pickle
from pathlib import Path

import faiss


def inspect_index_dir(index_dir: Path, max_docs: int) -> None:
    faiss_path = index_dir / "index.faiss"
    pkl_path = index_dir / "index.pkl"

    print(f"\n=== {index_dir.name} ===")

    if not faiss_path.exists() or not pkl_path.exists():
        print("Missing index.faiss or index.pkl")
        return

    idx = faiss.read_index(str(faiss_path))
    print(f"faiss_dim: {idx.d}")
    print(f"faiss_vectors: {idx.ntotal}")

    with pkl_path.open("rb") as f:
        payload = pickle.load(f)

    docstore = None
    id_map = None

    if isinstance(payload, tuple) and len(payload) >= 2:
        docstore = payload[0]
        id_map = payload[1]
    elif isinstance(payload, dict):
        docstore = payload.get("docstore")
        id_map = payload.get("index_to_docstore_id")

    docs = getattr(docstore, "_dict", {}) if docstore is not None else {}
    print(f"doc_count: {len(docs)}")
    print(f"id_map_count: {len(id_map) if isinstance(id_map, dict) else 'n/a'}")

    if not docs:
        return

    print("sample_docs:")
    for i, doc in enumerate(docs.values(), start=1):
        meta = getattr(doc, "metadata", {}) or {}
        excerpt = (getattr(doc, "page_content", "") or "").replace("\n", " ").strip()
        excerpt = excerpt[:200]
        print(f"  [{i}] source={meta.get('source', 'n/a')} | file_type={meta.get('file_type', 'n/a')} | page={meta.get('page', meta.get('page_number', 'n/a'))}")
        print(f"      excerpt={excerpt}")
        if i >= max_docs:
            break


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect FAISS index folders")
    parser.add_argument(
        "index_dir",
        nargs="?",
        default="data/index",
        help="Path to one index folder or to data/index root",
    )
    parser.add_argument("--max-docs", type=int, default=3, help="How many sample docs to print")
    args = parser.parse_args()

    target = Path(args.index_dir)
    if not target.exists():
        raise SystemExit(f"Path not found: {target}")

    if (target / "index.faiss").exists() and (target / "index.pkl").exists():
        inspect_index_dir(target, max_docs=args.max_docs)
        return

    dirs = [p for p in target.iterdir() if p.is_dir()]
    if not dirs:
        print("No index directories found")
        return

    for index_dir in sorted(dirs):
        inspect_index_dir(index_dir, max_docs=args.max_docs)


if __name__ == "__main__":
    main()
