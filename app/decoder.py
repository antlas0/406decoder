#!/usr/bin/env python3

import os
import datetime
import subprocess
import argparse
import requests
import tempfile
import logging

# Configure logging
logging.basicConfig(
    format="[%(asctime)s][%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S%z",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def reset_dvbt():
    """Resets the DVB-T USB device if detected."""
    devices = subprocess.check_output("lsusb", shell=True).decode().split("\n")
    for line in devices:
        parts = line.split()
        if len(parts) > 6 and "Realtek" in line:
            bus, dev = parts[1], parts[3][:-1]
            if parts[5] in ["2832", "2838"]:
                os.system(f"./reset_usb /dev/bus/usb/{bus}/{dev}")


def send_telegram(date: str, telegram_token: str, telegram_chatid: str) -> bool:
    """Sends an alert message to a Telegram chat."""
    message = f"Alerte Balise 406\nDate et Heure (UTC) du decodage: {date}"
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    data = {"chat_id": telegram_chatid, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        logger.error(str(e))
        return False
    else:
        return True


def touch(fname:str):
    if os.path.exists(fname):
        os.utime(fname, None)
    else:
        open(fname, 'a').close()


def scan_frequencies(f1_scan: int, f2_scan: int, ppm: int = 0, osm: bool = False, telegram_token: str = None, telegram_chatid: str = None, directory: str = None):
    """Scans the given frequency range and decodes signals."""
    code_filepath = os.path.join(directory, "code")
    trame_filepath = os.path.join(directory, "trame")
    logpower_filepath = os.path.join(directory, "log_power.csv")

    for file in [code_filepath, trame_filepath, logpower_filepath]:
        logger.info(file)
        touch(file)

    decode_command = "./dec406_V7 --100 --M3 --une_minute"
    if osm:
        decode_command += " --osm"

    power_command = f"rtl_power -p {ppm} -f {f1_scan}:{f2_scan}:400 -i55 -P -O -1 -e55 -w hamming {logpower_filepath} 2>/dev/null"
    
    while True:
        reset_dvbt()
        freq_found = False
        logger.info(f"Scan {f1_scan}...{f2_scan}")
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S%z")
        logger.info(f"...PATIENTER...")
        while not freq_found:
            try:
                subprocess.check_output(power_command)
            except subprocess.CalledProcessError as e:
                logger.error(f"Could not identify frequency {e}")
                return
            else:
                pass
            try:
                with open(logpower_filepath, "r") as f:
                    lines = f.readlines()
            except FileNotFoundError:
                logger.warning("[reset dvb-t ...]")
                reset_dvbt()
                continue
            
            max_signal = -200
            frq = 0
            for line in lines:
                parts = line.strip().split(",")
                freqs = list(map(float, parts[6:]))
                max_db = max(freqs, default=-200)
                if max_db > max_signal:
                    max_signal = max_db
                    frq = float(parts[2]) + freqs.index(max_db) * float(parts[4])
            
            if max_signal > -200:
                freq_found = True
                logger.info(f"\nFréquence: {frq/1e6:.3f}MHz Niveau: {max_signal:.1f}dB")
        
        while True:
            logger.info("Lancement du Decodage")
            build_command:list = []
            build_command.append(f"timeout 56s rtl_fm -p {ppm} -M fm -s 12k -f {frq} 2>/dev/null")
            build_command.append(f"sox -t raw -r 12k -e s -b 16 -c 1 - -t wav - lowpass 3000 highpass 400 2>/dev/null")
            build_command.append(f"{decode_command} 1>{trame_filepath} 2>{code_filepath}")

            full_command:str = "|".join(build_command)

            os.system(full_command)
            
            found = False
            try:
                with open(code_filepath, "r") as f:
                    if "TROUVE" in f.read():
                        found = True
            except FileNotFoundError:
                pass
            
            display_trame(trame_filepath)
            if found:
                if telegram_token and telegram_chatid:
                    send_telegram(date, telegram_token, telegram_chatid)
            else:
                break


def display_trame(filepath: str):
    """Displays the contents of the decoded trame file."""
    try:
        with open(filepath, "r") as f:
            logger.info(f.read())
    except FileNotFoundError:
        pass


def main():
    """Parses command-line arguments and initiates frequency scanning."""
    parser = argparse.ArgumentParser(description="Scanner la fréquence des balises 406MHz.")
    parser.add_argument("-s", "--freq-start", type=int, help="Fréquence de départ", action="store", default=406e6)
    parser.add_argument("-e", "--freq-end", type=int, help="Fréquence de fin", action="store", default=407e6)
    parser.add_argument("--ppm", type=int, default=0, help="Décalage PPM")
    parser.add_argument("--osm", action="store_true", help="Activer osm")
    parser.add_argument("-T", "--telegram-token", help="Telegram bot token")
    parser.add_argument("-C", "--telegram-chatid", help="Telegram chat ID")
    parser.add_argument("-O", "--output-directory", help="Output directory, default automatically generated.", default=None)
    args = parser.parse_args()

    output_directory = args.output_directory or tempfile.mkdtemp()
    logger.info(f"Output directory: {output_directory}")
    
    if not os.path.isdir(output_directory):
        logger.error(f"Output directory {output_directory} not found, aborting")
        return
    
    scan_frequencies(args.freq_start, args.freq_end, args.ppm, args.osm, args.telegram_token, args.telegram_chatid, output_directory)
    
if __name__ == "__main__":
    main()
