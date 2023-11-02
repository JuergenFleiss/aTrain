from .app import run_app
from .load_resources import download_all_resources
import argparse

def cli():
    parser = argparse.ArgumentParser(prog='aTrain', description='A GUI tool to transcribe audio with Whisper')
    parser.add_argument("command", choices=['init', 'start'], help="Command for aTrain to perform.")
    args = parser.parse_args()

    if args.command == "init":
        print("Downloading ffmpeg and all models:")
        download_all_resources()
    if args.command == "start":
        print("Starting aTrain")
        run_app()

if __name__ == "__main__":
    cli()