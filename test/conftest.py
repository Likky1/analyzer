import pytest
import shutil
from pathlib import Path

file_path = "test\\file_with_clickbate.csv"

@pytest.fixture
def multiple_csv_files():
    """Фикстура для создания нескольких CSV файлов"""
    files = []
    files.append(file_path)
    for i in range(3):
        f=shutil.copy(file_path, f"{i}.csv")
        files.append(f)

    yield files
    for file in files[1:]:
        Path(file).unlink()

@pytest.fixture
def clickbait_videos_sample():
    """Фикстура с образцом кликбейтных видео"""
    return [
        {'title': 'Секрет который скрывают тимлиды', 'ctr': 25, 'retention_rate': 22},
        {'title': 'Очень длинное название видео которое превышает 60 символов и должно быть обрезано', 'ctr': 22.5, 'retention_rate': 28},
        {'title': 'Как я задолжал ревьюеру 1000 строк кода', 'ctr': 21, 'retention_rate': 35},
        {'title': 'Купил джуну макбук и он уволился', 'ctr': 19, 'retention_rate': 38}
    ]
