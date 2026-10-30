import os
import json
import dropbox
from PIL import Image
import io
import urllib.parse

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

def get_category_from_name(filename):
    name = filename.lower()
    if 'portrait' in name or 'портрет' in name:
        return 'portrait'
    elif 'cinema' in name or 'кино' in name or 'film' in name:
        return 'cinema'
    elif 'fashion' in name or 'фешн' in name or 'фэшн' in name:
        return 'fashion'
    elif 'lifestyle' in name or 'лайфстайл' in name:
        return 'lifestyle'
    elif 'noir' in name or 'нуар' in name:
        return 'noir'
    elif 'surreal' in name or 'сюрреализм' in name:
        return 'surreal'
    return 'other'

def sync():
    portfolio_data = []
    valid_filenames = set()

    try:
        result = dbx.files_list_folder("", recursive=True)
        entries = list(result.entries)
        while result.has_more:
            result = dbx.files_list_folder_continue(result.cursor)
            entries.extend(result.entries)
    except Exception as e:
        print(f"Ошибка при сканировании Dropbox: {e}")
        return

    # Собираем реальные имена папок первого уровня внутри папки приложения
    folders_map = {}
    for entry in entries:
        if isinstance(entry, dropbox.files.FolderMetadata):
            parts = entry.path_lower.strip("/").split("/")
            if len(parts) == 1: # Папка прямо в корне папки приложения Dropbox
                folders_map[entry.path_lower] = entry.name

    files = [
        e for e in entries
        if isinstance(e, dropbox.files.FileMetadata) and e.name.lower().endswith(VALID_EXT)
    ]
    files.sort(key=lambda x: x.client_modified, reverse=True)

    for entry in files:
        parts = entry.path_lower.strip("/").split("/")
        folder_slug = "all"
        folder_display_name = "Все работы"

        # Если файл лежит внутри подпапки первого уровня
        if len(parts) > 1:
            root_folder_path = "/" + parts[0]
            if root_folder_path in folders_map:
                real_name = folders_map[root_folder_path]
                folder_slug = urllib.parse.quote(real_name.lower())
                folder_display_name = real_name

        name_without_ext = os.path.splitext(entry.name)[0]
        dest_filename = f"{abs(hash(entry.path_lower))}_{name_without_ext}.webp"
        dest_path = os.path.join(IMAGES_DIR, dest_filename)
        valid_filenames.add(dest_filename)

        if not os.path.exists(dest_path):
            print(f"Скачивание и сжатие: {entry.name}")
            _, res = dbx.files_download(entry.path_lower)
            with Image.open(io.BytesIO(res.content)) as img:
                img.thumbnail((1920, 1920))
                img.save(dest_path, "WEBP", quality=85)

        tag = get_category_from_name(entry.name)
        
        portfolio_data.append({
            "src": f"images/{dest_filename}",
            "title": name_without_ext.replace("_", " ").replace("-", " "),
            "category": tag,
            "folder": folder_slug,
            "folderName": folder_display_name
        })

    for existing_file in os.listdir(IMAGES_DIR):
        if existing_file not in valid_filenames:
            try:
                os.remove(os.path.join(IMAGES_DIR, existing_file))
            except:
                pass

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(portfolio_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    sync()
