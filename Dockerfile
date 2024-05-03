#FROM debian:latest
FROM python:3.11-bullseye

RUN apt update && apt install -y ffmpeg
# python3 python3-pip python3-venv git -y
#RUN pip3 install torch==2.0.0+cu118 torchaudio==2.0.0 --index-url https://download.pytorch.org/whl/cu118
#TODO: Change the following:
RUN pip3 install aTrain@git+https://github.com/SjDayg/aTrain.git --extra-index-url https://download.pytorch.org/whl/cu118
RUN aTrain init

EXPOSE 80

ENTRYPOINT ["aTrain" "startserver"]
