
import sys
import glob
import json
import pathlib
import shutil


def change_kernel(notebook):
    """
    Vanillafy the kernelspec.
    """
    new_kernelspec = {
        "display_name": "Python 3 (ipykernel)",
        "language": "python",
        "name": "python3",
    }
    notebook['metadata']['kernelspec'].update(new_kernelspec)
    return notebook


def main(path):
    """
    Process the IPYNB files in path, save in place (side-effect).
    """
    fnames = glob.glob(path.strip('/') + '/[!_]*.ipynb')  # Not files with underscore.
    outpath = pathlib.Path('_notebooks')
    if outpath.exists():
        shutil.rmtree(outpath)
    outpath.mkdir(exist_ok=True)

    for fname in fnames:
        with open(fname, encoding='utf-8') as f:
            notebook = json.loads(f.read())

        new_nb = change_kernel(notebook)
        filepart = pathlib.Path(fname).name

        with open(outpath / filepart, 'w') as f:
            _ = f.write(json.dumps(new_nb))

    return


if __name__ == '__main__':
    print(sys.argv[1])
    _ = main(sys.argv[1])