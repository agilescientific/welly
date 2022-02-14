
import sys
import glob
import re


def simplify_credits(html):
    """
    Replace the credit part of the HTML footer. Return the new text.
    """
    s = r"Created using <a href=\"https://www\.sphinx.+?Furo theme</a>."
    pattern = re.compile(s, flags=re.DOTALL)

    new_s = '<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>'
    new_s += ' | Created using Sphinx & Furo'

    return pattern.sub(new_s, html)

def main(path):
    """
    Process the HTML files in path, save in place (side-effect).
    """
    fnames = glob.glob(path.strip('/') + '/*.html')
    for fname in fnames:
        with open(fname, 'r+') as f:
            html = f.read()

            new_html = simplify_credits(html)

            f.seek(0)
            f.write(new_html)
            f.truncate()
    return


if __name__ == '__main__':
    _ = main(sys.argv[1])
