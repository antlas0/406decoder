# Dockerfile
FROM python:3.11.11-bookworm

RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    rtl-sdr \
    sox \
    libsox-fmt-all \
    pulseaudio \
    usbutils \
    && rm -rf /var/lib/apt/lists/*

COPY ./app /app
WORKDIR /app
RUN gcc ./dec406_V7.c -lm -o ./dec406_V7 \
    && chmod u+x ./dec406_V7
RUN gcc ./reset_usb.c -lm -o ./reset_usb \
    && chmod u+x ./reset_usb

RUN python -m pip install -r requirements.txt

CMD ["python3", "decoder.py"]
