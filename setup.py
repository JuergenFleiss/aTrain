from setuptools import setup, find_packages
import platform

system = platform.system()
if system == "Windows":
    torch = "torch@https://download.pytorch.org/whl/cu118/torch-2.0.0%2Bcu118-cp310-cp310-win_amd64.whl#sha256=5ee2b7c19265b9c869525c378fcdf350510b8f3fc08af26da1a2587a34cea8f5"
if system == "Linux":
    torch = "torch@https://download.pytorch.org/whl/cu118/torch-2.0.0%2Bcu118-cp310-cp310-linux_x86_64.whl#sha256=4b690e2b77f21073500c65d8bb9ea9656b8cb4e969f357370bbc992a3b074764"
if system == "Darwin":
    torch = "torch==2.0.0"

setup(
    name='aTrain',
    version='1.1.0',
    readme="README.md",
    python_requires=">=3.10",
    install_requires=[
        torch,
        "torchaudio==2.0.1",
        "faster-whisper>=0.8",
        "transformers",
        "ffmpeg-python>=0.2",
        "pandas",
        "whisperx @ git+https://github.com/m-bain/whisperx.git@v3.1.1",
        "Flask==2.3.2",
        "pywebview==4.2.2",
        "screeninfo==0.8.1",
        "wakepy==0.7.2",
        "show-in-file-manager==1.1.4"
    ],
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': ['aTrain = aTrain.app:run_app',]
    }
)


