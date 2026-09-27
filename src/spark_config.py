import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HADOOP_HOME = Path(r"C:\hadoop")


def configure_spark_environment():
    os.environ["HADOOP_HOME"] = str(HADOOP_HOME)

    hadoop_bin = HADOOP_HOME / "bin"
    os.environ["PATH"] = str(hadoop_bin) + os.pathsep + os.environ.get("PATH", "")

    python_exe = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

    os.environ["PYSPARK_PYTHON"] = str(python_exe)
    os.environ["PYSPARK_DRIVER_PYTHON"] = str(python_exe)
