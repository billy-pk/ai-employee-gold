"""
Vault Helpers - Common operations for vault file management.

Provides utilities for reading/writing markdown files with YAML frontmatter,
moving files between vault folders, and generating unique IDs.
"""

import os
import re
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

import yaml
from dotenv import load_dotenv

load_dotenv()


def get_vault_path() -> Path:
    """Get the vault path from environment variable."""
    return Path(os.getenv('VAULT_PATH', '/mnt/d/AI_EMPLOYEE_VAULT'))


def get_vault_folder(folder_name: str) -> Path:
    """Get a specific folder within the vault."""
    folder = get_vault_path() / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def generate_unique_id(prefix: str = "") -> str:
    """
    Generate a unique ID for items.

    Args:
        prefix: Optional prefix for the ID (e.g., "EMAIL", "FILE", "PLAN")

    Returns:
        Unique ID string like "EMAIL_a1b2c3d4" or just "a1b2c3d4"
    """
    short_uuid = uuid.uuid4().hex[:8]
    if prefix:
        return f"{prefix}_{short_uuid}"
    return short_uuid


def generate_timestamp_id(prefix: str = "") -> str:
    """
    Generate a timestamp-based ID for items.

    Args:
        prefix: Optional prefix for the ID

    Returns:
        ID like "EMAIL_20260202_143022" or "20260202_143022"
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if prefix:
        return f"{prefix}_{timestamp}"
    return timestamp


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Full markdown content with optional frontmatter

    Returns:
        Tuple of (frontmatter_dict, body_content)
    """
    frontmatter = {}
    body = content

    # Match frontmatter between --- markers
    match = re.match(r'^---\n(.*?)\n---\n?(.*)', content, re.DOTALL)
    if match:
        try:
            frontmatter = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            frontmatter = {}
        body = match.group(2)

    return frontmatter, body


def format_frontmatter(metadata: dict, body: str) -> str:
    """
    Format metadata and body into markdown with YAML frontmatter.

    Args:
        metadata: Dictionary of frontmatter fields
        body: Markdown body content

    Returns:
        Complete markdown string with frontmatter
    """
    if metadata:
        frontmatter = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
        return f"---\n{frontmatter}---\n\n{body}"
    return body


def read_markdown_file(filepath: Path) -> tuple[dict, str]:
    """
    Read a markdown file and parse its frontmatter.

    Args:
        filepath: Path to the markdown file

    Returns:
        Tuple of (frontmatter_dict, body_content)

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    content = filepath.read_text(encoding='utf-8')
    return parse_frontmatter(content)


def write_markdown_file(filepath: Path, metadata: dict, body: str) -> None:
    """
    Write a markdown file with YAML frontmatter.

    Args:
        filepath: Path to write the file
        metadata: Dictionary of frontmatter fields
        body: Markdown body content
    """
    content = format_frontmatter(metadata, body)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding='utf-8')


def update_frontmatter(filepath: Path, updates: dict) -> None:
    """
    Update specific fields in a file's frontmatter.

    Args:
        filepath: Path to the markdown file
        updates: Dictionary of fields to update/add
    """
    metadata, body = read_markdown_file(filepath)
    metadata.update(updates)
    write_markdown_file(filepath, metadata, body)


def update_status(filepath: Path, new_status: str) -> None:
    """
    Update the status field in a file's frontmatter.

    Args:
        filepath: Path to the markdown file
        new_status: New status value (e.g., "pending", "processed", "completed")
    """
    update_frontmatter(filepath, {'status': new_status})


def move_to_folder(filepath: Path, dest_folder: str, preserve_name: bool = True) -> Path:
    """
    Move a file to a different vault folder.

    Args:
        filepath: Path to the file to move
        dest_folder: Name of destination folder (e.g., "Done", "Approved")
        preserve_name: If True, keep original filename; if False, may rename

    Returns:
        Path to the file in its new location
    """
    dest_dir = get_vault_folder(dest_folder)
    dest_path = dest_dir / filepath.name

    # Handle name conflicts
    if dest_path.exists() and not preserve_name:
        stem = filepath.stem
        suffix = filepath.suffix
        counter = 1
        while dest_path.exists():
            dest_path = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1

    shutil.move(str(filepath), str(dest_path))
    return dest_path


def copy_to_folder(filepath: Path, dest_folder: str) -> Path:
    """
    Copy a file to a different vault folder.

    Args:
        filepath: Path to the file to copy
        dest_folder: Name of destination folder

    Returns:
        Path to the copied file
    """
    dest_dir = get_vault_folder(dest_folder)
    dest_path = dest_dir / filepath.name

    # Handle name conflicts
    if dest_path.exists():
        stem = filepath.stem
        suffix = filepath.suffix
        counter = 1
        while dest_path.exists():
            dest_path = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1

    shutil.copy2(str(filepath), str(dest_path))
    return dest_path


def list_files_in_folder(folder_name: str, pattern: str = "*.md") -> list[Path]:
    """
    List files in a vault folder matching a pattern.

    Args:
        folder_name: Name of the vault folder
        pattern: Glob pattern to match (default: "*.md")

    Returns:
        List of matching file paths, sorted by modification time (newest first)
    """
    folder = get_vault_folder(folder_name)
    files = list(folder.glob(pattern))
    return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)


def get_pending_items(folder_name: str = "Needs_Action") -> list[Path]:
    """
    Get items with status: pending in a folder.

    Args:
        folder_name: Folder to search (default: Needs_Action)

    Returns:
        List of file paths with pending status
    """
    pending = []
    for filepath in list_files_in_folder(folder_name):
        try:
            metadata, _ = read_markdown_file(filepath)
            if metadata.get('status') == 'pending':
                pending.append(filepath)
        except Exception:
            continue
    return pending


def archive_file(filepath: Path, add_timestamp: bool = True) -> Path:
    """
    Archive a file to the Done folder.

    Args:
        filepath: Path to the file to archive
        add_timestamp: If True, add timestamp to filename

    Returns:
        Path to the archived file
    """
    if add_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_name = f"{filepath.stem}_{timestamp}{filepath.suffix}"
        dest_dir = get_vault_folder("Done")
        dest_path = dest_dir / new_name
        shutil.move(str(filepath), str(dest_path))
        return dest_path
    else:
        return move_to_folder(filepath, "Done")


def safe_filename(name: str, max_length: int = 50) -> str:
    """
    Convert a string to a safe filename.

    Args:
        name: Original string
        max_length: Maximum length of the result

    Returns:
        Safe filename string
    """
    # Replace unsafe characters with underscores
    safe = re.sub(r'[^\w\s.-]', '_', name)
    # Replace whitespace with underscores
    safe = re.sub(r'\s+', '_', safe)
    # Remove consecutive underscores
    safe = re.sub(r'_+', '_', safe)
    # Trim underscores from ends
    safe = safe.strip('_')
    # Truncate if too long
    if len(safe) > max_length:
        safe = safe[:max_length].rstrip('_')
    return safe


def log_to_vault(message: str, log_name: str = "system") -> None:
    """
    Append a timestamped message to a vault log file.

    Args:
        message: Message to log
        log_name: Name of the log file (without extension)
    """
    logs_dir = get_vault_folder("Logs")
    log_file = logs_dir / f"{log_name}.log"

    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {message}\n"

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)
