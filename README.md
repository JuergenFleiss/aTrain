# aTrain 
## Accessible Transcription of Interviews

## System requirements
You need a Windows system.
No Linux or MacOS support.

## Installation for developers ⚙️

#### You need to have python version 3.10 and git installed
If you need help with installing that, look at these resources:  
https://www.python.org/downloads/release/python-31011/  
https://git-scm.com/download/win/  

#### Clone this repo
```
git clone https://github.com/Juergen-J-F/aTrain.git
```

#### Change directory into aTrain
```
cd aTrain
```
#### Setup the virtual environment
```
python -m venv venv
```
If you have multiple python versions installed specify version 3.10
```
py -3.10 -m venv venv
```
#### Activate the virtual environment
```
.\venv\Scripts\activate
```
#### Install pytorch and cuda
```
pip install torch==2.0.0+cu117 torchvision==0.15.1+cu117 torchaudio==2.0.1 --index-url https://download.pytorch.org/whl/cu117
```
#### Install [whisperX](https://github.com/m-bain/whisperX)
```
pip install git+https://github.com/m-bain/whisperx.git
```
#### Install flask and pywebview + other dependencies
```
pip install flask pywebview screeninfo
```
#### Run the app
```
python app.py
```


## Licenses

Following python libraries were used for this project:  
LIBRARY -> Licencse  
  
The UI was designed using [TailwindCSS](https://tailwindcss.com/) and [DaisyUI](https://daisyui.com/).  
The GIFs and Icons are from [tenor](https://tenor.com/) and [flaticon](https://www.flaticon.com/). 