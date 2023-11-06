from setuptools import setup, find_packages
import platform

system = platform.system()
if system in ["Windows","Linux"]:
    torch = "torch==2.0.0+cu118"
if system == "Darwin":
    torch = "torch==2.0.0"

setup(
    name='aTrain',
    version='1.1.0',
    readme="README.md",
    license="LICENSE",
    python_requires=">=3.10",
    install_requires=[
        torch,
        "torchaudio==2.0.1",
        "faster-whisper>=0.8",
        "transformers",
        "ffmpeg-python>=0.2",
        "pandas",
        "pyannote.audio==3.0.0",
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


