# Known Issues & Workarounds

## 1. Local Postgres Initialization in Tests
- **Issue**: macOS Homebrew installs versioned PostgreSQL binaries in `/opt/homebrew/opt/postgresql@16/bin` outside default `PATH`.
- **Workaround**: `api/tests/conftest.py` automatically scans Homebrew versioned paths and boots a throwaway cluster.

## 2. Unix Socket Path Length on macOS
- **Issue**: macOS limits unix domain socket paths to ~103 characters.
- **Workaround**: Pytest fixtures allocate sockets in `/tmp/pgs...` short paths rather than deep temporary directories.

## 3. High Memory Usage during Bulk Vector Indexing
- **Issue**: Indexing large docsets (>10,000 chunks) in memory can spike RAM.
- **Workaround**: The refiner batches documents and uses disk-backed SQLite/Chroma persistence.
