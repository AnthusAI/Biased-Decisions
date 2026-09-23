"""Report statistics on neutral cue versions per task."""
import json
import gzip
from pathlib import Path
from collections import defaultdict

def get_stats(task_slug: str, root: Path = Path("/Users/home/Projects/Biased-Decisions-neutral")) -> dict:
    """Get build statistics for neutral cue on a task."""
    versions_path = root / "tasks" / task_slug / "versions" / "neutral.jsonl"

    if not versions_path.exists():
        return {"error": f"No versions file for {task_slug}"}

    stats = {"task": task_slug, "blank": {}, "they": {}, "total": {}}
    rows_by_version = defaultdict(int)
    verbs_adjusted_by_version = defaultdict(int)

    with open(versions_path, "r") as f:
        for line in f:
            row = json.loads(line)
            version = row["metadata"].get("version")
            if version:
                rows_by_version[version] += 1

    stats["rows_by_version"] = dict(rows_by_version)
    stats["total_rows"] = sum(rows_by_version.values())

    return stats


if __name__ == "__main__":
    tasks = [
        "paralegal-attorney", "nurse-physician", "surgeon-physician",
        "teacher-professor", "journalist-professor", "architect-interior-designer",
        "dietitian-physician",
    ]

    root = Path("/Users/home/Projects/Biased-Decisions-neutral")
    all_stats = []

    for task_slug in tasks:
        stats = get_stats(task_slug, root)
        all_stats.append(stats)

        if "error" in stats:
            print(f"{task_slug}: {stats['error']}")
        else:
            print(f"{task_slug}:")
            print(f"  Total rows: {stats['total_rows']}")
            if stats['rows_by_version']:
                for version in ("blank", "they"):
                    count = stats['rows_by_version'].get(version, 0)
                    print(f"  {version}: {count}")
