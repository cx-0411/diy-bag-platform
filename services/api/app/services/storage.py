import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile
from app.core.config import get_settings
class StorageService:
    def __init__(self, root: str | None = None) -> None: self.root = Path(root or get_settings().storage_path); self.root.mkdir(parents=True, exist_ok=True)
    def save_upload(self, upload: UploadFile) -> tuple[str, int]:
        suffix = Path(upload.filename or '').suffix.lower(); key = f'{uuid.uuid4()}{suffix}'; target = self.root / key
        with target.open('wb') as output: shutil.copyfileobj(upload.file, output)
        return key, target.stat().st_size
    def url(self, key: str) -> str: return f'/api/files/{key}'
