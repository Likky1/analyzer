import pytest
import tempfile
import shutil
from pathlib import Path

# Импортируем функции из основного модуля
from mai import (
    read_csv_file,
    process_files,
    generate_clickbate,
    choose_report,
)

file_path = "test\\file_with_clickbate.csv"
file_path_without_clickbate = "test\\file_without_clickbate.csv"
empty_file_path = "test\\empty_file.csv"
boundary_file_path = "test\\file_with_limit.csv"

# ==================== ФИКСТУРЫ ====================

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


# ==================== ТЕСТЫ ДЛЯ read_csv_file ====================

class TestReadCSVFile:
    """Тесты для функции read_csv_file"""

    def test_read_valid_csv(self):
        """Тест чтения корректного CSV файла"""
        data = read_csv_file(file_path)

        assert len(data) == 10  #
        assert data[0]['title'] == 'Я бросил IT и стал фермером'
        assert data[0]['ctr'] == '18.2'
        assert data[0]['retention_rate'] == '35'

    def test_read_empty_csv(self):
        """Тест чтения пустого CSV файла"""
        data = read_csv_file(empty_file_path)
        assert len(data) == 0, "файл пуст"


# ==================== ТЕСТЫ ДЛЯ process_files ====================

class TestProcessFiles:
    """Тесты для функции process_files"""

    def test_single_file_with_clickbait(self):
        """Тест обработки одного файла с кликбейтными видео"""
        result = process_files([str(file_path)])

        assert len(result) == 5
        assert result[0]['title'] == 'Секрет который скрывают тимлиды'
        assert result[0]['ctr'] == 25
        assert result[1]['title'] == 'Почему продакшн упал в пятницу вечером '
        assert result[1]['ctr'] == 24
        assert result[2]['title'] == 'Как я неделю не мыл кружку и выгорел'
        assert result[2]['ctr'] == 23

    def test_sorting_by_ctr_descending(self):
        """Тест сортировки по убыванию CTR"""
        result = process_files([str(file_path)])

        for i in range(len(result) - 1):
            assert result[i]['ctr'] >= result[i + 1]['ctr']

    def test_multiple_files(self, multiple_csv_files):
        """Тест обработки нескольких файлов"""
        file_paths = [str(f) for f in multiple_csv_files]
        result = process_files(file_paths)

        # 4 файла * 5 кликбейтных видео = 20 видео
        assert len(result) == 20
        # Проверяем сортировку
        for i in range(len(result) - 1):
            assert result[i]['ctr'] >= result[i + 1]['ctr']

    def test_file_without_clickbait(self):
        """Тест файла без кликбейтных видео"""
        result = process_files([str(file_path_without_clickbate)])
        assert len(result) == 0

    def test_boundary_values(self):
        """Тест граничных условий"""
        result = process_files([str(boundary_file_path)])
        titles = [v['title'] for v in result]
        assert 'Граница 1' not in titles
        assert 'Граница 2' in titles
        assert 'Граница 3' not in titles
        assert 'Граница 4' in titles
        assert len(result) == 2


    def test_empty_file_paths(self):
        """Тест с пустым списком файлов"""
        result = process_files([])
        assert len(result) == 0


# ==================== ТЕСТЫ ДЛЯ generate_clickbate ====================

class TestGenerateClickbate:
    """Тесты для функции generate_clickbate"""

    def test_report_with_clickbait_videos(self, capsys):
        """Тест генерации отчета с кликбейтными видео"""
        generate_clickbate(file_path)
        captured = capsys.readouterr()

        # Проверяем наличие заголовков
        assert "Название видео" in captured.out
        assert "CTR" in captured.out
        assert "retention_rate" in captured.out

        # Проверяем наличие данных
        assert "Секрет который скрывают тимлиды " in captured.out
        assert "25" in captured.out
        assert "32" in captured.out  # retention_rate как int

        assert "Как я неделю не мыл кружку и выгорел  " in captured.out
        assert "23" in captured.out

        # Проверяем форматирование
        assert "|" in captured.out  # Таблица с границами
        assert "-" in captured.out  # Линии таблицы

    def test_report_without_clickbait(self, capsys):
        """Тест генерации отчета без кликбейтных видео"""
        generate_clickbate([])
        captured = capsys.readouterr()

        assert "Кликбейтные видео не найдены" in captured.out
        assert "|" not in captured.out  # Нет таблицы

    def test_report_title_truncation(self, capsys):
        """Тест обрезания длинных названий"""
        generate_clickbate(file_path)
        captured = capsys.readouterr()

        # Проверяем, что длинное название обрезано
        assert "Очень длинное название видео которое превышает 60 символов и должно быть обрезано" not in captured.out
        assert "..." in captured.out


# ==================== ТЕСТЫ ДЛЯ choose_report ====================

class TestChooseReport:
    """Тесты для функции choose_report"""

    def test_clickbait_report_type(self, capsys, clickbait_videos_sample):
        """Тест выбора отчета clickbait"""
        choose_report(clickbait_videos_sample, 'clickbait')
        captured = capsys.readouterr()

        # Должен быть вызван generate_clickbate
        assert "Название видео" in captured.out
        assert "CTR" in captured.out

    def test_unknown_report_type(self, capsys):
        """Тест неизвестного типа отчета"""
        choose_report([], 'unknown_type')
        captured = capsys.readouterr()

        assert "Отчета пока не существует" in captured.out

    def test_clickbait_with_empty_list(self, capsys):
        """Тест clickbait отчета с пустым списком"""
        choose_report([], 'clickbait')
        captured = capsys.readouterr()

        assert "Кликбейтные видео не найдены" in captured.out


# ==================== ТЕСТЫ ПРОИЗВОДИТЕЛЬНОСТИ ====================

@pytest.mark.slow
class TestPerformance:
    """Тесты производительности"""

    def test_large_file_processing(self):
        """Тест обработки большого файла (10000 записей)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("title,ctr,retention_rate\n")
            for i in range(10000):
                ctr = 10 + (i % 20)  # CTR от 10 до 30
                retention = 30 + (i % 30)  # Удержание от 30 до 60
                f.write(f"Видео {i},{ctr},{retention}\n")
            temp_path = Path(f.name)

        try:
            import time
            start_time = time.time()
            result = process_files([str(temp_path)])
            end_time = time.time()

            processing_time = end_time - start_time
            assert processing_time < 1.0  # Должно обработать менее чем за секунду
            assert len(result) > 0
        finally:
            temp_path.unlink()


# ==================== ЗАПУСК ТЕСТОВ ====================

if __name__ == "__main__":
    pytest.main([__file__, '-v', '--tb=short'])