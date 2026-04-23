import argparse
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any
from tabulate import tabulate

def read_csv_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Читает CSV файл и возвращает список словарей с данными.

    Args:
        file_path: Путь к CSV файлу

    Returns:
        Список словарей, где ключи - названия колонок
    """
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
    except FileNotFoundError:
        print(f"Ошибка: Файл {file_path} не найден")
        raise

    return data


def process_files(file_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Обрабатывает все CSV файлы и собирает кликбейтные видео. После чего сортирует по убыванию CTR

    Args:
        file_paths: Список путей к CSV файлам

    Returns:
        Список кликбейтных видео с нужными полями
    """
    all_clickbait_videos = []

    for file_path in file_paths:
        data = read_csv_file(Path(file_path))

        # Фильтруем кликбейтные видео из текущего файла
        for row in data:
            ctr = float(row.get('ctr'))
            retention = float(row.get('retention_rate'))
            if ctr > 15 and retention < 40:
                clickbait_video = {
                    'title': row.get('title'),
                    'ctr': float(row.get('ctr')),
                    'retention_rate': float(row.get('retention_rate'))
                }
                all_clickbait_videos.append(clickbait_video)

    # Сортируем по убыванию CTR
    all_clickbait_videos.sort(key=lambda x: x['ctr'], reverse=True)

    return all_clickbait_videos

def generate_clickbate(clickbait_videos: List[Dict[str, Any]]) -> None:
    """
        Генерирует и выводит отчет в консоль.

        Args:
            clickbait_videos: Список кликбейтных видео
            report_type: Тип отчета
        """


    if not clickbait_videos:
        print("\n Кликбейтные видео не найдены.")
        return

    # Подготовка данных для tabulate
    table_data = []
    for video in (clickbait_videos):
        table_data.append([
            video['title'][:60] + '...' if len(video['title']) > 60 else video['title'],
            f"{video['ctr']:.2f}",
            int(video['retention_rate']),
        ])

    # Заголовки таблицы
    headers = ["Название видео", "CTR", "retention_rate"]

    # Вывод таблицы
    print(tabulate(table_data, headers=headers, tablefmt="grid"))



def choose_report(clickbait_videos: List[Dict[str, Any]], report_type: str) -> None:
    """
    В случае добавления других вариантов отчета позволит определить вид отчета

    Args:
        clickbait_videos: Список кликбейтных видео
        report_type: Тип отчета (в данном случае 'clickbait')
    """


    if report_type == 'clickbait':
        generate_clickbate(clickbait_videos)
    else:
        print("Отчета пока не существует")

    return None


def main():
    """Главная функция приложения."""
    parser = argparse.ArgumentParser(
        description='CLI приложение для анализа метрик YouTube видео',
    )

    parser.add_argument(
        '--files',
        nargs='+',
        required=True,
        help='Список CSV файлов для анализа (можно указать несколько через пробел)'
    )

    parser.add_argument(
        '--report',
        type=str,
        required=True,
        help='Тип отчета'
    )

    args = parser.parse_args()

    # Проверяем, что указаны файлы
    if not args.files:
        print("Ошибка: Не указаны файлы для обработки")
        sys.exit(1)


    # Обрабатываем файлы и собираем кликбейтные видео
    clickbait_videos = process_files(args.files)

    # Генерируем отчет
    choose_report(clickbait_videos, args.report)


if __name__ == "__main__":
    main()
