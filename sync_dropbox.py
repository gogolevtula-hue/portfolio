import os
import json
import dropbox
from PIL import Image
import io

APP_KEY = os.environ["DROPBOX_APP_KEY"]
APP_SECRET = os.environ["DROPBOX_APP_SECRET"]
REFRESH_TOKEN = os.environ["DROPBOX_REFRESH_TOKEN"]

IMAGES_DIR = "images"
JSON_PATH = "images.json"
VALID_EXT = ('.png', '.jpg', '.jpeg', '.webp')

os.makedirs(IMAGES_DIR, exist_ok=True)

dbx = dropbox.Dropbox(
    oauth2_refresh_token=REFRESH_TOKEN,
    app_key=APP_KEY,
    app_secret=APP_SECRET
)

def sync():
    result = dbx.files_list_folder("")
    entries = list(result.entries)
    while result.has_more:
        result = dbx.files_list_folder_continue(result.cursor)
        entries.extend(result.entries)

    files = [
        e for e in entries
        if isinstance(e, dropbox.files.FileMetadata) and e.name.lower().endswith(VALID_EXT)
    ]
    files.sort(key=lambda x: x.client_modified, reverse=True)

    portfolio_data = []
    valid_filenames = set()

    for entry in files:
        name_without_ext = os.path.splitext(entry.name)[0]
        dest_filename = f"{name_without_ext}.webp"
        dest_path = os.path.join(IMAGES_DIR, dest_filename)
        valid_filenames.add(dest_filename)

        if not os.path.exists(dest_path):
            print(f"Скачивание и сжатие: {entry.name}")
            _, res = dbx.files_download(entry.path_lower)
            with Image.open(io.BytesIO(res.content)) as img:
                img.thumbnail((1920, 1920))
                img.save(dest_path, "WEBP", quality=85)

        portfolio_data.append({
            "src": f"images/{dest_filename}",
            "title": name_without_ext.replace("_", " ").replace("-", " ")
        })

    # Удаляем из папки GitHub картинки, которых больше нет в Dropbox
    for existing_file in os.listdir(IMAGES_DIR):
        if existing_file not in valid_filenames:
            os.remove(os.path.join(IMAGES_DIR, existing_file))
            print(f"Удалено: {existing_file}")

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(portfolio_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    sync()
