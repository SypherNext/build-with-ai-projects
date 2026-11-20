#!/usr/bin/env python3
"""Scan a project directory and generate a professional README.md using Claude Haiku."""

import os
import json
import ast
import re
import argparse
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
import anthropic

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError(
        "ANTHROPIC_API_KEY not found. Set it in .env or export it."
    )

MODEL_NAME = "claude-haiku-5-5"
MAX_TOKENS_PER_RUN = 4096
MAX_ITERATIONS = 3


def find_project_root(path: str = ".") -> Path:
    """Resolve the target directory to an absolute path."""
    root = Path(path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")
    return root


def read_file_safe(filepath: Path, max_lines: int = 200) -> Optional[str]:
    """Read a file safely, returning None if it fails or is too large."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                lines.append(line)
            return "".join(lines)
    except Exception:
        return None


def detect_project_type(root: Path) -> str:
    """Detect the project type by looking for key files."""
    indicators = {
        "python-library": ["setup.py", "setup.cfg"],
        "python-package": ["pyproject.toml"],
        "web-framework": [
            "manage.py", "app.py", "main.py", "package.json"
        ],
        "cli-tool": ["cli.py", "cli/", "console_scripts"],
        "data-pipeline": ["Dockerfile", "requirements.txt"],
        "documentation": ["mkdocs.yml", "conf.py", "index.rst"],
    }
    filenames = {f.name for f in root.iterdir() if f.is_file()}
    dirnames = {d.name for d in root.iterdir() if d.is_dir()}

    for proj_type, markers in indicators.items():
        for marker in markers:
            if marker in filenames or marker.rstrip("/") in dirnames:
                return proj_type
    return "general"


def extract_python_metadata(root: Path) -> Dict:
    """Extract metadata from Python project files."""
    metadata = {
        "name": None,
        "version": None,
        "description": None,
        "dependencies": [],
        "entry_points": [],
    }

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        content = read_file_safe(pyproject)
        if content:
            name_match = re.search(
                r'name\s*=\s*"([^"]+)"', content
            )
            ver_match = re.search(
                r'version\s*=\s*"([^"]+)"', content
            )
            desc_match = re.search(
                r'description\s*=\s*"([^"]+)"', content
            )
            if name_match:
                metadata["name"] = name_match.group(1)
            if ver_match:
                metadata["version"] = ver_match.group(1)
            if desc_match:
                metadata["description"] = desc_match.group(1)

    setup_py = root / "setup.py"
    if setup_py.exists():
        content = read_file_safe(setup_py)
        if content:
            dep_match = re.findall(
                r'"([^"]+[>=<]+[^"]*)"', content
            )
            metadata["dependencies"].extend(dep_match)

    requirements = root / "requirements.txt"
    if requirements.exists():
        content = read_file_safe(requirements)
        if content:
            deps = [
                line.strip()
                for line in content.split("\n")
                if line.strip()
                and not line.startswith("#")
                and not line.startswith("-")
            ]
            metadata["dependencies"].extend(deps)

    for py_file in root.rglob("*.py"):
        content = read_file_safe(py_file, max_lines=50)
        if content:
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        metadata["entry_points"].append(
                            f"{py_file.relative_to(root)}::{node.name}"
                        )
            except SyntaxError:
                pass

    return metadata


def scan_structure(root: Path, max_depth: int = 3) -> Dict:
    """Build a tree of the project directory structure."""
    structure = {}
    for item in sorted(root.iterdir()):
        if item.name.startswith(".") or item.name == "venv":
            continue
        if item.name == "__pycache__":
            continue
        if item.is_dir():
            sub = scan_structure(item, max_depth - 1)
            if sub or max_depth > 1:
                structure[item.name + "/"] = sub
        else:
            structure[item.name] = None
    return structure


def scan_project(path: str = ".") -> Dict:
    """Run the full scan and return all extracted information."""
    root = find_project_root(path)
    project_type = detect_project_type(root)
    metadata = extract_python_metadata(root)
    structure = scan_structure(root)

    key_files = {}
    for pattern in [
        "README.md", "CONTRIBUTING.md", "CHANGELOG.md",
        "LICENSE", ".gitignore", "Dockerfile",
        "Makefile", "docker-compose.yml",
    ]:
        candidate = root / pattern
        if candidate.exists():
            key_files[pattern] = read_file_safe(candidate, max_lines=50)

    return {
        "project_type": project_type,
        "metadata": metadata,
        "structure": structure,
        "key_files": key_files,
    }


def build_project_summary(scan_result: Dict) -> str:
    """Turn the scan result into a concise text summary for the LLM."""
    meta = scan_result["metadata"]
    parts = [
        f"Project type: {scan_result['project_type']}",
    ]
    if meta.get("name"):
        parts.append(f"Name: {meta['name']}")
    if meta.get("version"):
        parts.append(f"Version: {meta['version']}")
    if meta.get("description"):
        parts.append(f"Description: {meta['description']}")
    if meta.get("dependencies"):
        parts.append(
            f"Dependencies: {', '.join(meta['dependencies'][:15])}"
        )
    if meta.get("entry_points"):
        parts.append(
            f"Entry points: {', '.join(meta['entry_points'][:10])}"
        )

    parts.append("\nDirectory structure:")
    parts.append(json.dumps(scan_result["structure"], indent=2))

    return "\n".join(parts)


SYSTEM_PROMPT = """You are a senior technical writer specializing in open-source
documentation. Your task is to generate a professional README.md for a software
project based on metadata about the project.

Output ONLY valid Markdown. Use these sections in order:

1. # Project name (from metadata) — one-line description below the heading
2. ## Description — 2-3 paragraphs explaining what the project does and why it exists
3. ## Installation — step-by-step pip, npm, or manual install instructions
4. ## Usage — basic usage examples with code blocks
5. ## Project Structure — a tree view of the directory layout
6. ## API Reference — document each public function or module found in the entry points
7. ## Dependencies — list key dependencies and what they are used for
8. ## Contributing — brief guidelines for contributors
9. ## License — placeholder for license information

Use fenced code blocks with language tags for all code examples.
Use bold for UI labels and file names.
Do not invent features the project does not have.
If information is missing, skip that section rather than guessing.
"""


def build_prompt(scan_result: Dict) -> str:
    """Build the complete prompt for the LLM."""
    project_summary = build_project_summary(scan_result)
    key_files_section = ""
    if scan_result.get("key_files"):
        for fname, content in scan_result["key_files"].items():
            if content:
                key_files_section += (
                    f"\n<file name=\"{fname}\">\n"
                    f"{content}\n</file>\n"
                )

    prompt = f"""{SYSTEM_PROMPT}

<project_scan>
{project_summary}
</project_scan>

<key_files>
{key_files_section}
</key_files>

Generate the README.md now. Start directly with the # heading."""
    return prompt


def generate_readme(prompt: str) -> str:
    """Send the prompt to Claude Haiku and return the generated README."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS_PER_RUN,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        return response.content[0].text
    except anthropic.APIError as e:
        print(f"API error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


def save_readme(content: str, output_path: str, force: bool = False) -> bool:
    """Write the generated README to a file, respecting existing files."""
    path = Path(output_path)

    if path.exists() and not force:
        print(
            f"README.md already exists at {path}. "
            f"Use --force to overwrite."
        )
        return False

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"README.md generated at {path}")
    return True


def format_readme_output(content: str) -> str:
    """Clean up and normalize the generated Markdown output."""
    content = content.strip()

    if not content.startswith("#"):
        content = "# Project\n\n" + content

    if not content.endswith("\n"):
        content += "\n"

    return content


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate a professional README.md for any project."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the project directory (default: current dir)",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing README.md without asking",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backup of existing README.md",
    )
    parser.add_argument(
        "--model",
        default=MODEL_NAME,
        help=f"Claude model to use (default: {MODEL_NAME})",
    )
    return parser.parse_args()


def backup_existing_readme(path: Path) -> Optional[Path]:
    """Back up an existing README.md if present."""
    readme = path / "README.md"
    if readme.exists():
        backup = path / "README.md.backup"
        backup.write_text(readme.read_text(encoding="utf-8"))
        print(f"Backed up existing README.md to {backup}")
        return backup
    return None


def main():
    args = parse_args()

    print(f"Scanning project at: {args.path}")
    scan_result = scan_project(args.path)

    print(
        f"Detected project type: {scan_result['project_type']}"
    )
    if scan_result["metadata"].get("name"):
        print(f"Project name: {scan_result['metadata']['name']}")

    print("Building prompt for Claude Haiku...")
    prompt = build_prompt(scan_result)

    print("Generating README with Claude Haiku (this may take a moment)...")
    try:
        raw_output = generate_readme(prompt)
    except Exception as e:
        print(f"Failed to generate README: {e}")
        return

    readme_content = format_readme_output(raw_output)

    if not args.no_backup:
        backup_existing_readme(Path(args.path))

    success = save_readme(
        readme_content,
        str(Path(args.path) / "README.md"),
        force=args.force,
    )

    if success:
        print("Done! Your README.md is ready.")


if __name__ == "__main__":
    main()
