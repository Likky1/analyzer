import os


def run_click():
    """
        Служит для удобного запуска приложения.
            Собирает файлы из папки FILES в корне приложения и запрашивает название отчета
        """


    main_file = 'main.py'
    csv_folder = 'FILES'
    files = os.listdir(csv_folder)
    file_paths = ''
    report_type = input('Введите название отчета: ')
    for file in files:
        file_paths += f'{os.path.join(csv_folder, file)} '
    run_command = f'python {main_file} --files {file_paths} --report {report_type}'
    os.system(run_command)

run_click()