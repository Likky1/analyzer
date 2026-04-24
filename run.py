import os


def run_cli():
    main_file = 'mai.py'
    csv_folder = 'FILES'
    files = os.listdir(csv_folder)
    file_paths = ''
    for file in files:
        file_paths += f'{os.path.join(csv_folder, file)} '
    run_command = f'python {main_file} --files {file_paths} --report clickbait'
    os.system(run_command)

run_cli()