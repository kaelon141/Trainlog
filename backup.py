#!/usr/bin/env python3
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
from zoneinfo import ZoneInfo

# ─── Configuration ──────────────────────────────────────────────────────────────

# Folder where live DBs live, and where backups go
SRC_DIR = Path("databases")
BASE_BACKUP_DIR = Path("backup")

# List of DB filenames
SIMPLE_DBS = ["auth.db", "error.db"]
FILTERED_DBS = [("main.db", "trip", "uid"), ("path.db", "paths", "trip_id")]

# Max parameters per SQLite query (keep below 999)
CHUNK_SIZE = 900

# ─── Progress Bar Class ─────────────────────────────────────────────────────────


class ProgressBar:
    def __init__(self, total: int, description: str = "", width: int = 40):
        self.total = total
        self.current = 0
        self.description = description
        self.width = width
        self.start_time = time.time()
        self.last_update = 0

    def update(self, amount: int = 1):
        """Update progress by amount and display if enough time has passed."""
        self.current = min(self.current + amount, self.total)

        # Update display at most every 0.1 seconds to avoid flickering
        current_time = time.time()
        if current_time - self.last_update >= 0.1 or self.current == self.total:
            self._display()
            self.last_update = current_time

    def _display(self):
        """Display the current progress bar."""
        if self.total == 0:
            percentage = 100
            filled_length = self.width
        else:
            percentage = (self.current / self.total) * 100
            filled_length = int(self.width * self.current // self.total)

        bar = "█" * filled_length + "▒" * (self.width - filled_length)

        # Calculate time estimates
        elapsed = time.time() - self.start_time
        if self.current > 0 and self.current < self.total:
            rate = self.current / elapsed
            remaining = (self.total - self.current) / rate
            time_str = f" | ETA: {self._format_time(remaining)}"
        elif self.current == self.total:
            time_str = f" | Done in {self._format_time(elapsed)}"
        else:
            time_str = " | Calculating..."

        # Build the progress line
        progress_line = f"\r{self.description} |{bar}| {percentage:5.1f}% ({self.current}/{self.total}){time_str}"

        # Print and ensure we don't leave trailing characters
        print(progress_line.ljust(80), end="", flush=True)

        if self.current == self.total:
            print()  # New line when complete

    def _format_time(self, seconds: float) -> str:
        """Format seconds into human-readable time."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"


# ─── Helper Functions ────────────────────────────────────────────────────────────


def now_iso_date():
    """Return today's date in YYYY-MM-DD for Europe/Oslo."""
    tz = ZoneInfo("Europe/Oslo")
    return datetime.now(tz).strftime("%Y-%m-%d")


def connect_readonly(path: Path):
    """Open a read-only, immutable SQLite URI connection."""
    uri = f"file:{path}?mode=ro&immutable=1"
    return sqlite3.connect(uri, uri=True)


def connect_writable(path: Path):
    """Open or create a writable SQLite file."""
    return sqlite3.connect(path)


def get_table_row_count(conn: sqlite3.Connection, table: str) -> int:
    """Get the number of rows in a table."""
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    return cur.fetchone()[0]


def get_all_tables_row_count(conn: sqlite3.Connection) -> int:
    """Get total row count across all user tables."""
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    total = 0
    for (table,) in cur.fetchall():
        total += get_table_row_count(conn, table)
    return total


def copy_schema_and_data(
    src_conn, dst_conn, table_filter=None, progress_callback: Optional[Callable] = None
):
    """
    Copy all tables/indexes/triggers/views from src to dst.
    Skips sqlite_sequence and any tables rejected by table_filter(name)->bool.
    """
    src = src_conn.cursor()
    dst = dst_conn.cursor()

    # Grab all user-and-meta objects (tables, indexes, triggers, views)
    src.execute("""
        SELECT type, name, sql 
          FROM sqlite_master 
         WHERE name NOT LIKE 'sqlite_%' 
           AND sql IS NOT NULL
         ORDER BY type='table' DESC, type='index', type;
    """)
    schema_objects = src.fetchall()

    # Create schema objects
    for obj_type, name, sql in schema_objects:
        if table_filter and not table_filter(name, obj_type):
            continue
        dst.execute(sql)
    dst_conn.commit()

    # Copy table data with progress tracking
    src.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    tables = [row[0] for row in src.fetchall()]

    for tbl in tables:
        if table_filter and not table_filter(tbl, "table"):
            continue

        # Get all rows for this table
        rows = src.execute(f"SELECT * FROM {tbl}").fetchall()
        if not rows:
            continue

        # Insert rows and update progress
        placeholders = ", ".join(["?"] * len(rows[0]))
        dst.executemany(f"INSERT INTO {tbl} VALUES ({placeholders})", rows)

        if progress_callback:
            progress_callback(len(rows))

    dst_conn.commit()


def get_ids(src_path: Path, table: str, column: str) -> set:
    """Fetch the set of values of `column` from `table` in src_path."""
    conn = connect_readonly(src_path)
    cur = conn.cursor()
    cur.execute(f"SELECT DISTINCT {column} FROM {table}")
    ids = {row[0] for row in cur.fetchall()}
    conn.close()
    return ids


def chunked(iterable, size):
    """Yield successive chunks from iterable of length ≤ size."""
    it = list(iterable)
    for i in range(0, len(it), size):
        yield it[i : i + size]


# ─── Backup Routines ────────────────────────────────────────────────────────────


def backup_simple(db_name: str, dst_folder: Path):
    """Copy schema + all data from a simple DB (no cross-filtering)."""
    src = SRC_DIR / db_name
    dst = dst_folder / db_name

    print(f"Analyzing {db_name}...")

    # Get total row count for progress tracking
    with connect_readonly(src) as src_conn:
        total_rows = get_all_tables_row_count(src_conn)

    if total_rows == 0:
        print(f"✅ {db_name} is empty, skipping.")
        return

    # Create progress bar
    progress = ProgressBar(total_rows, f"Backing up {db_name}")

    def update_progress(rows_processed):
        progress.update(rows_processed)

    # Perform backup with progress tracking
    with connect_readonly(src) as src_conn, connect_writable(dst) as dst_conn:
        copy_schema_and_data(src_conn, dst_conn, progress_callback=update_progress)


def backup_filtered(
    main_db: str, table: str, column: str, valid_ids: set, dst_folder: Path
):
    """
    Copy schema + all data *except* `table`, then create `table` and copy only rows
    whose `column` is in valid_ids (in chunks).
    """
    src = SRC_DIR / main_db
    dst = dst_folder / main_db

    print(f"Analyzing {main_db}...")

    with connect_readonly(src) as src_conn:
        # Get total rows excluding the filtered table
        total_other_rows = 0
        cur = src_conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        for (tbl,) in cur.fetchall():
            if tbl != table:
                total_other_rows += get_table_row_count(src_conn, tbl)

        # Get count of rows we'll copy from the filtered table
        if valid_ids:
            # Estimate based on a sample to avoid creating huge IN clauses
            sample_size = min(100, len(valid_ids))
            sample_ids = list(valid_ids)[:sample_size]
            qmarks = ",".join("?" for _ in sample_ids)
            sample_count = cur.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {column} IN ({qmarks})",
                tuple(sample_ids),
            ).fetchone()[0]
            # Extrapolate to full set
            filtered_rows = int(sample_count * len(valid_ids) / sample_size)
        else:
            filtered_rows = 0

        total_rows = total_other_rows + filtered_rows

    if total_rows == 0:
        print(f"✅ {main_db} would be empty after filtering, skipping.")
        return

    # Create progress bar
    progress = ProgressBar(total_rows, f"Backing up {main_db} (filtered)")

    with connect_readonly(src) as src_conn, connect_writable(dst) as dst_conn:
        # 1) Copy everything *except* our filtered table
        def filter_out(name, obj_type):
            return not (obj_type == "table" and name == table)

        def update_progress_other(rows_processed):
            progress.update(rows_processed)

        copy_schema_and_data(
            src_conn,
            dst_conn,
            table_filter=filter_out,
            progress_callback=update_progress_other,
        )

        # 2) Now create the filtered table schema itself
        schema_sql = src_conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()[0]
        dst_conn.execute(schema_sql)

        # 3) Copy filtered data in chunks
        insert_cur = dst_conn.cursor()
        for chunk in chunked(valid_ids, CHUNK_SIZE):
            qmarks = ",".join("?" for _ in chunk)
            rows = src_conn.execute(
                f"SELECT * FROM {table} WHERE {column} IN ({qmarks})", tuple(chunk)
            ).fetchall()
            if rows:
                ph = ",".join("?" for _ in rows[0])
                insert_cur.executemany(f"INSERT INTO {table} VALUES ({ph})", rows)
                progress.update(len(rows))

        dst_conn.commit()


# ─── Main Script ────────────────────────────────────────────────────────────────


def main():
    print("🔄 Starting database backup...\n")

    # 1) Prepare destination folder
    date_str = now_iso_date()
    dst = BASE_BACKUP_DIR / date_str
    dst.mkdir(parents=True, exist_ok=True)
    print(f"📁 Backing up to folder: {dst}\n")

    # 2) Simple DBs
    for db in SIMPLE_DBS:
        backup_simple(db, dst)
        print()  # Add spacing between databases

    # 3) Compute valid trip IDs = intersection of main.trip.uid and path.paths.trip_id
    print("🔍 Computing valid trip IDs...")
    main_ids = get_ids(SRC_DIR / "main.db", "trip", "uid")
    path_ids = get_ids(SRC_DIR / "path.db", "paths", "trip_id")
    valid = main_ids & path_ids

    print(f"   Found {len(main_ids)} trip IDs in main.db")
    print(f"   Found {len(path_ids)} trip IDs in path.db")
    print(f"   Valid intersection: {len(valid)} trip IDs")

    if not valid:
        print("⚠️  Warning: no matching trip IDs between main.db and path.db")
    print()

    # 4) Filtered DBs
    backup_filtered("main.db", "trip", "uid", valid, dst)
    print()
    backup_filtered("path.db", "paths", "trip_id", valid, dst)
    print()

    print("✅ Backup complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Backup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Backup failed: {e}", file=sys.stderr)
        sys.exit(1)
