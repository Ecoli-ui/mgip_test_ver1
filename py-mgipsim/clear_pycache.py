import os, shutil

test_directory = './Test'
for dirpath, dirnames, filenames in os.walk(test_directory):
    if '__pycache__' in dirnames:
        pycache_path = os.path.join(dirpath, '__pycache__')
        shutil.rmtree(pycache_path)

pymgipsim_directory = os.path.join(os.path.dirname(os.getcwd()), 'pymgipsim')
if os.path.isdir(os.path.join(pymgipsim_directory, '__pycache__')):
    shutil.rmtree(os.path.join(pymgipsim_directory, '__pycache__'))

for directory in ['.idea', '.vscode']:
    dir_path = os.path.join(pymgipsim_directory, directory)
    if os.path.isdir(dir_path):
        shutil.rmtree(dir_path)

for dirpath, dirnames, filenames in os.walk(pymgipsim_directory):
    if '__pycache__' in dirnames:
        pycache_path = os.path.join(dirpath, '__pycache__')
        shutil.rmtree(pycache_path)

