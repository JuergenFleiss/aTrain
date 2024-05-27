from setuptools import setup, find_packages
from distutils.util import convert_path
import platform

system = platform.system()
if system in ["Windows","Linux"]:
    torch = "torch==2.2.0+cu121"
if system == "Darwin":
    torch = "torch==2.2.0"

main_ns = {}
ver_path = convert_path('aTrain/version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

setup(
    name='aTrain',
    version=main_ns['__version__'],
    readme="README.md",
    license="LICENSE",
    python_requires=">=3.10",
    install_requires=[
        torch,
        "torchaudio==2.2.0",
        "faster-whisper==1.0.2",
        "transformers",
        "ffmpeg-python>=0.2",
        "pandas",
        "pyannote.audio==3.2.0",
        "Flask==2.3.2",
        "pywebview==4.2.2",
        "flaskwebgui",
        "screeninfo==0.8.1",
        "wakepy==0.7.2",
        "show-in-file-manager==1.1.4"
    ],
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': ['aTrain = aTrain:cli',]
    }
)


