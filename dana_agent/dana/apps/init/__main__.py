"""dana-init: Copy default config.json to current directory for customization."""

from pathlib import Path
import shutil


def main():
    src = Path(__file__).parent.parent.parent / "config.json"  # dana/config.json
    dest = Path.cwd() / "dana" / "config.json"

    if dest.exists():
        print(f"Config already exists at {dest}")
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print(f"Created {dest} — customize it for your project")
    print(f"Set DANA_CONFIG_PATH={dest} to use it")


if __name__ == "__main__":
    main()
