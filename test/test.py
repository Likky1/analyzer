import pytest

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
        assert result[1]['title'] == 'Как я задолжал ревьюеру 1000 строк кода'
        assert result[1]['ctr'] == 21
        assert result[2]['title'] == 'Купил джуну макбук и он уволился'
        assert result[2]['ctr'] == 19

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

    def test_report_with_clickbait_videos(self, capsys, clickbait_videos_sample):
        """Тест генерации отчета с кликбейтными видео"""
        generate_clickbate(clickbait_videos_sample)
        captured = capsys.readouterr()

        # Проверяем наличие заголовков
        assert "Название видео" in captured.out
        assert "CTR" in captured.out
        assert "retention_rate" in captured.out

        # Проверяем наличие данных
        assert "Секрет который скрывают тимлиды " in captured.out
        assert "25" in captured.out
        assert "22" in captured.out  # retention_rate как int

        assert "Как я задолжал ревьюеру 1000 строк кода" in captured.out
        assert "21" in captured.out

        # Проверяем форматирование
        assert "|" in captured.out  # Таблица с границами
        assert "-" in captured.out  # Линии таблицы

    def test_report_without_clickbait(self, capsys):
        """Тест генерации отчета без кликбейтных видео"""
        generate_clickbate([])
        captured = capsys.readouterr()

        assert "Кликбейтные видео не найдены" in captured.out
        assert "|" not in captured.out  # Нет таблицы

    def test_report_title_truncation(self, capsys, clickbait_videos_sample):
        """Тест обрезания длинных названий"""
        generate_clickbate(clickbait_videos_sample)
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


# ==================== ЗАПУСК ТЕСТОВ ====================

if __name__ == "__main__":
    pytest.main(['-v'])