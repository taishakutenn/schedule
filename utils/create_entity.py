# Script for quickly creating an entity template
import os
import sys
from config.settings import ROOT_PATH


def create_entity(name: str):
    # Create folder
    folder_path = os.path.join(ROOT_PATH, "api", name)
    os.makedirs(folder_path, exist_ok=True)

    # Create files into the same folder
    files = [f"{name}_DAL.py", f"{name}_handlers.py", f"{name}_pydantic.py", f"{name}_services.py"]
    for filename in files:
        filepath = os.path.join(folder_path, filename)
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("# Auto-generated file\n")

    print(f"✅ Folder '{name}' and files were created in: {folder_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python create_entity.py <имя-папки>")
        sys.exit(1)

    create_entity(sys.argv[1])