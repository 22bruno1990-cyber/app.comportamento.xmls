import os
import sys
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent / "projeto_nfe_mvp"
os.chdir(APP_DIR)
sys.path.insert(0, str(APP_DIR))

from docsmart_app import main


if __name__ == "__main__":
    main()
