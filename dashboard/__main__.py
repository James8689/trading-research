from pathlib import Path
import os
from .server import serve

if __name__ == '__main__':
    raise SystemExit(serve(Path(os.environ.get('DASHBOARD_ROOT', '.'))))
