import os
import sys
from file_sca import FileSCA

if len(sys.argv) < 2:
    print("error: Please provide a filename")
    sys.exit(1)
filename = sys.argv[1]


# TODO account for multiline strings when porting this for resume
# - i.e. prevent false positives


files_to_check = []
errors = []

if os.path.isfile(filename) and filename.endswith(".py"):
    files_to_check.append(filename)
elif os.path.isdir(filename):
    for dir_path, dir_names, file_names in os.walk(filename):
        for f in file_names:
            if f.endswith(".py"):
                files_to_check.append(os.path.join(dir_path, f))
else:
    print("Error: Can't find given path")
    sys.exit(1)

files_to_check.sort()
for f in files_to_check:
    # TODO refactor to make static method
    sca = FileSCA(f)
    sca.analyze()
    errors = errors + [e[1] for e in sca.errors]

for e in errors:
    print(e)
