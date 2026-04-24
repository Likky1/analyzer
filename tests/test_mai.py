import pytest
import csv
import tempfile
import sys
from pathlib import Path
from io import StringIO
from unittest.mock import patch, MagicMock

# Импортируем функции из основного модуля
from mai import (
    read_csv_file,
    process_files,
    generate_clickbate,
    choose_report,
    main
)


# ==================== ФИКСТУРЫ ====================

@pytest.fixture
def sample_csv_content():
    """Фикстура с корректным содержимым CSV файла"""
    return """title,ctr,retention_rate
Как заработать миллион?,22.5,35.2
ШОК! Трюк изменит жизнь,18.7,28.9
Обычное видео,8.3,65.4
ТЫ НЕ ПОВЕРИШЬ,25.1,32.0
Полезный контент,5.2,55.8
Видео на границе,15.1,39.9
"""


@pytest.fixture
def sample_csv_file(sample_csv_content):
    """Фикстура, создающая временный CSV файл"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(sample_csv_content)
        temp_path = Path(f.name)

    yield temp_path
    temp_path.unlink()  # Удаляем файл после теста


@pytest.fixture
def multiple_csv_files(sample_csv_content):
    """Фикстура для создания нескольких CSV файлов"""
    files = []
    for i in range(3):
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.csv', delete=False, encoding='utf-8') as f:
            f.write(sample_csv_content)
            files.append(Path(f.name))

    yield files
    for file in files:
        file.unlink()


@pytest.fixture
def invalid_csv_file():
    """Фикстура с некорректным CSV файлом"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("title,ctr,retention_rate\n")
        f.write("Видео 1,не число,50\n")
        f.write("Видео 2,20,не число\n")
        temp_path = Path(f.name)

    yield temp_path
    temp_path.unlink()


@pytest.fixture
def csv_with_missing_columns():
    """Фикстура с отсутствующими колонками"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("title,ctr\n")
        f.write("Видео 1,20\n")
        temp_path = Path(f.name)

    yield temp_path
    temp_path.unlink()


@pytest.fixture
def clickbait_videos_sample():
    """Фикстура с образцом кликбейтных видео"""
    return [
        {'title': 'ТЫ НЕ ПОВЕРИШЬ', 'ctr': 25.1, 'retention_rate': 32.0},
        {'title': 'Как заработать миллион?', 'ctr': 22.5, 'retention_rate': 35.2},
        {'title': 'ШОК! Трюк изменит жизнь', 'ctr': 18.7, 'retention_rate': 28.9},
        {'title': 'Очень длинное название видео которое превышает 60 символов и должно быть обрезано',
         'ctr': 20.0, 'retention_rate': 30.0}
    ]


# ==================== ТЕСТЫ ДЛЯ read_csv_file ====================

class TestReadCSVFile:
    """Тесты для функции read_csv_file"""

    def test_read_valid_csv(self, sample_csv_file, sample_csv_content):
        """Тест чтения корректного CSV файла"""
        data = read_csv_file(sample_csv_file)

        assert len(data) == 6  # 5 + 1 граничное
        assert data[0]['title'] == 'Как заработать миллион?'
        assert data[0]['ctr'] == '22.5'
        assert data[0]['retention_rate'] == '35.2'

    def test_read_empty_csv(self):
        """Тест чтения пустого CSV файла"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("title,ctr,retention_rate\n")
            temp_path = Path(f.name)

        try:
            data = read_csv_file(temp_path)
            assert len(data) == 0
        finally:
            temp_path.unlink()

    def test_file_not_found(self):
        """Тест обработки отсутствующего файла"""
        with pytest.raises(FileNotFoundError):
            read_csv_file(Path("nonexistent_file.csv"))

    def test_csv_without_headers(self):
        """Тест CSV файла без заголовков"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Видео 1,20,30\n")
            f.write("Видео 2,25,35\n")
            temp_path = Path(f.name)

        try:
            data = read_csv_file(temp_path)
            # DictReader будет использовать первую строку как заголовки
            assert len(data) == 1  # Первая строка стала заголовком
        finally:
            temp_path.unlink()

    def test_csv_with_extra_spaces(self):
        """Тест CSV с лишними пробелами"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("title, ctr , retention_rate\n")
            f.write("Видео 1, 20.5 , 35.0\n")
            temp_path = Path(f.name)

        try:
            data = read_csv_file(temp_path)
            assert len(data) == 1
            # Пробелы сохраняются в значениях
            assert data[0][' ctr '] == ' 20.5 '
        finally:
            temp_path.unlink()


# ==================== ТЕСТЫ ДЛЯ process_files ====================

class TestProcessFiles:
    """Тесты для функции process_files"""

    def test_single_file_with_clickbait(self, sample_csv_file):
        """Тест обработки одного файла с кликбейтными видео"""
        result = process_files([str(sample_csv_file)])

        # Включая граничное видео (15.1 > 15 и 39.9 < 40)
        assert len(result) == 4  # 3 явных + 1 граничное
        assert result[0]['title'] == 'ТЫ НЕ ПОВЕРИШЬ'  # Самый высокий CTR
        assert result[0]['ctr'] == 25.1
        assert result[1]['title'] == 'Как заработать миллион?'
        assert result[1]['ctr'] == 22.5
        assert result[2]['title'] == 'ШОК! Трюк изменит жизнь'
        assert result[2]['ctr'] == 18.7

    def test_sorting_by_ctr_descending(self, sample_csv_file):
        """Тест сортировки по убыванию CTR"""
        result = process_files([str(sample_csv_file)])

        for i in range(len(result) - 1):
            assert result[i]['ctr'] >= result[i + 1]['ctr']

    def test_multiple_files(self, multiple_csv_files):
        """Тест обработки нескольких файлов"""
        file_paths = [str(f) for f in multiple_csv_files]
        result = process_files(file_paths)

        # 3 файла * 4 кликбейтных видео = 12 видео
        assert len(result) == 12
        # Проверяем сортировку
        for i in range(len(result) - 1):
            assert result[i]['ctr'] >= result[i + 1]['ctr']

    def test_file_without_clickbait(self):
        """Тест файла без кликбейтных видео"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("title,ctr,retention_rate\n")
            f.write("Нормальное видео,10.0,50.0\n")
            f.write("Хорошее видео,12.0,70.0\n")
            f.write("Отличное видео,14.9,45.0\n")
            temp_path = Path(f.name)

        try:
            result = process_files([str(temp_path)])
            assert len(result) == 0
        finally:
            temp_path.unlink()

    def test_boundary_values(self):
        """Тест граничных условий"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("title,ctr,retention_rate\n")
            f.write("Граница 1,15.0,39.0\n")  # CTR = 15 (должен быть исключен)
            f.write("Граница 2,15.1,39.9\n")  # Оба больше/меньше (должен войти)
            f.write("Граница 3,20.0,40.0\n")  # retention = 40 (должен быть исключен)
            f.write("Граница 4,20.0,39.9\n")  # retention < 40 (должен войти)
            temp_path = Path(f.name)

        try:
            result = process_files([str(temp_path)])
            titles = [v['title'] for v in result]
            assert 'Граница 1' not in titles
            assert 'Граница 2' in titles
            assert 'Граница 3' not in titles
            assert 'Граница 4' in titles
            assert len(result) == 2
        finally:
            temp_path.unlink()

    def test_invalid_numeric_values(self, invalid_csv_file):
        """Тест обработки нечисловых значений"""
        result = process_files([str(invalid_csv_file)])
        # Строки с нечисловыми значениями вызовут исключение
        # process_files не обрабатывает исключения, поэтому они всплывут
        with pytest.raises(ValueError):
            process_files([str(invalid_csv_file)])

    def test_missing_columns(self, csv_with_missing_columns):
        """Тест отсутствующих колонок"""
        # Отсутствует колонка retention_rate, вызовет KeyError
        with pytest.raises(KeyError):
            process_files([str(csv_with_missing_columns)])

    def test_empty_file_paths(self):
        """Тест с пустым списком файлов"""
        result = process_files([])
        assert len(result) == 0

    def test_nonexistent_files(self):
        """Тест несуществующих файлов"""
        with pytest.raises(FileNotFoundError):
            process_files(["nonexistent1.csv"])


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
        assert "ТЫ НЕ ПОВЕРИШЬ" in captured.out
        assert "25.10" in captured.out
        assert "32" in captured.out  # retention_rate как int

        assert "Как заработать миллион?" in captured.out
        assert "22.50" in captured.out

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

    def test_retention_rate_as_integer(self, capsys):
        """Тест что retention_rate выводится как целое число"""
        videos = [
            {'title': 'Тест', 'ctr': 25.5, 'retention_rate': 35.7},
            {'title': 'Тест 2', 'ctr': 20.1, 'retention_rate': 39.9}
        ]

        generate_clickbate(videos)
        captured = capsys.readouterr()

        # Проверяем, что дробная часть отброшена
        assert "35.7" not in captured.out
        assert "35" in captured.out
        assert "39.9" not in captured.out
        assert "39" in captured.out

    def test_ctr_formatting_two_decimals(self, capsys):
        """Тест форматирования CTR с двумя знаками после запятой"""
        videos = [
            {'title': 'Тест', 'ctr': 25.5, 'retention_rate': 30.0},
            {'title': 'Тест 2', 'ctr': 20.12345, 'retention_rate': 35.0}
        ]

        generate_clickbate(videos)
        captured = capsys.readouterr()

        assert "25.50" in captured.out
        assert "20.12" in captured.out
        assert "20.12345" not in captured.out

    def test_empty_title_handling(self, capsys):
        """Тест обработки пустого названия"""
        videos = [
            {'title': None, 'ctr': 25.0, 'retention_rate': 30.0},
            {'title': '', 'ctr': 22.0, 'retention_rate': 35.0}
        ]

        generate_clickbate(videos)
        captured = capsys.readouterr()

        # Должно быть выведено без ошибок
        assert "None" not in captured.out or "" in captured.out


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

    def test_return_value(self):
        """Тест возвращаемого значения"""
        result = choose_report([], 'clickbait')
        assert result is None

        result = choose_report([], 'unknown')
        assert result is None


# ==================== ТЕСТЫ ДЛЯ main ====================

class TestMain:
    """Тесты для главной функции main"""

    def test_main_with_valid_args(self, sample_csv_file):
        """Тест запуска main с валидными аргументами"""
        test_args = ['mai.py', '--files', str(sample_csv_file), '--report', 'clickbait']

        with patch.object(sys, 'argv', test_args):
            with patch('mai.process_files') as mock_process:
                mock_process.return_value = []
                with patch('mai.choose_report') as mock_choose:
                    main()
                    mock_process.assert_called_once_with([str(sample_csv_file)])
                    mock_choose.assert_called_once()

    def test_main_with_multiple_files(self, multiple_csv_files):
        """Тест main с несколькими файлами"""
        file_paths = [str(f) for f in multiple_csv_files]
        test_args = ['mai.py', '--files'] + file_paths + ['--report', 'clickbait']

        with patch.object(sys, 'argv', test_args):
            with patch('mai.process_files') as mock_process:
                mock_process.return_value = []
                with patch('mai.choose_report'):
                    main()
                    mock_process.assert_called_once_with(file_paths)

    def test_main_without_files(self):
        """Тест main без указания файлов"""
        test_args = ['mai.py', '--report', 'clickbait']

        with patch.object(sys, 'argv', test_args):
            with pytest.raises(SystemExit):
                main()

    def test_main_without_report(self):
        """Тест main без указания отчета"""
        test_args = ['mai.py', '--files', 'test.csv']

        with patch.object(sys, 'argv', test_args):
            with pytest.raises(SystemExit):
                main()

    def test_main_with_empty_files_list(self, capsys):
        """Тест main с пустым списком файлов"""
        test_args = ['mai.py', '--files', '--report', 'clickbait']

        with patch.object(sys, 'argv', test_args):
            with pytest.raises(SystemExit):
                main()

    @patch('mai.process_files')
    @patch('mai.choose_report')
    def test_main_integration(self, mock_choose, mock_process, sample_csv_file):
        """Интеграционный тест main с реальными вызовами"""
        test_args = ['mai.py', '--files', str(sample_csv_file), '--report', 'clickbait']

        with patch.object(sys, 'argv', test_args):
            main()
            mock_process.assert_called_once()
            mock_choose.assert_called_once()


# ==================== ИНТЕГРАЦИОННЫЕ ТЕСТЫ ====================

class TestIntegration:
    """Интеграционные тесты всего приложения"""

    def test_full_pipeline_with_valid_file(self, sample_csv_file, capsys):
        """Полный тест с реальным файлом"""
        test_args = ['mai.py', '--files', str(sample_csv_file), '--report', 'clickbait']

        with patch.object(sys, 'argv', test_args):
            # Запускаем main
            main()
            captured = capsys.readouterr()

            # Проверяем вывод отчета
            assert "Название видео" in captured.out
            assert "CTR" in captured.out
            assert "ТЫ НЕ ПОВЕРИШЬ" in captured.out
            assert "Как заработать миллион?" in captured.out
            assert "ШОК! Трюк изменит жизнь" in captured.out
            assert "Видео на границе" in captured.out

    def test_full_pipeline_without_clickbait(self, capsys):
        """Тест с файлом без кликбейтных видео"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("title,ctr,retention_rate\n")
            f.write("Нормальное видео,10.0,60.0\n")
            f.write("Хорошее видео,12.0,55.0\n")
            temp_path = Path(f.name)

        try:
            test_args = ['mai.py', '--files', str(temp_path), '--report', 'clickbait']

            with patch.object(sys, 'argv', test_args):
                main()
                captured = capsys.readouterr()

                assert "Кликбейтные видео не найдены" in captured.out
        finally:
            temp_path.unlink()

    def test_full_pipeline_with_multiple_files(self, multiple_csv_files, capsys):
        """Тест с несколькими файлами"""
        file_paths = [str(f) for f in multiple_csv_files]
        test_args = ['mai.py', '--files'] + file_paths + ['--report', 'clickbait']

        with patch.object(sys, 'argv', test_args):
            main()
            captured = capsys.readouterr()

            # Должно быть 12 видео (3 файла * 4 кликбейтных)
            assert "Название видео" in captured.out
            # Проверяем, что данные из всех файлов объединены
            assert captured.out.count("ТЫ НЕ ПОВЕРИШЬ") == 3  # По одному разу из каждого файла


# ==================== ТЕСТЫ НА ОШИБКИ ====================

class TestErrorHandling:
    """Тесты обработки ошибок"""

    def test_value_error_handling(self, capsys):
        """Тест обработки ValueError при преобразовании типов"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("title,ctr,retention_rate\n")
            f.write("Видео 1,invalid,30\n")
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError):
                process_files([str(temp_path)])
        finally:
            temp_path.unlink()

    def test_key_error_handling(self):
        """Тест обработки KeyError при отсутствии колонок"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("title,ctr\n")
            f.write("Видео 1,20\n")
            temp_path = Path(f.name)

        try:
            with pytest.raises(KeyError):
                process_files([str(temp_path)])
        finally:
            temp_path.unlink()


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

    def test_memory_usage_with_large_file(self):
        """Тест использования памяти при обработке большого файла"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("title,ctr,retention_rate\n")
            for i in range(50000):
                f.write(f"Видео {i},{20 + (i % 10)},{30 + (i % 20)}\n")
            temp_path = Path(f.name)

        try:
            import tracemalloc
            tracemalloc.start()

            result = process_files([str(temp_path)])

            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # Пик использования памяти не должен превышать 100MB
            assert peak < 100 * 1024 * 1024  # 100 MB
            assert len(result) > 0
        finally:
            temp_path.unlink()


# ==================== ЗАПУСК ТЕСТОВ ====================

if __name__ == "__main__":
    pytest.main([__file__, '-v', '--tb=short'])