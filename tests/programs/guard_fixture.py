"""Disposable repository copies for destructive failure-injection tests."""
import shutil
import subprocess
import tempfile
from pathlib import Path

def isolated_repository(test, source):
    temporary=tempfile.TemporaryDirectory()
    test.addCleanup(temporary.cleanup)
    root=Path(temporary.name)/'model'
    shutil.copytree(source,root,ignore=shutil.ignore_patterns('.git','__pycache__','run-output'))
    gitdir=subprocess.check_output(['git','rev-parse','--absolute-git-dir'],cwd=source,text=True).strip()
    (root/'.git').write_text('gitdir: '+gitdir+'\n')
    return root
