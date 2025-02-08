# 406decoder
Decodes 406M EIPRB data, based on already working code from [F4EHY](http://jgsenlis.free.fr/406_PI.html).


# How to install
First we need to install some prerequisites.
```bash
$ apt-get update && apt-get install -y \
    gcc \
    build-essential \
    rtl-sdr \
    sox \
    libsox-fmt-all \
    pulseaudio \
    usbutils
```

Then, everything is in the `app` folder, so once in it please call:
```bash
$ gcc ./dec406_V7.c -lm -o ./dec406_V7 \
    && chmod u+x ./dec406_V7
$ gcc ./reset_usb.c -lm -o ./reset_usb \
    && chmod u+x ./reset_usb

$ python -m pip install -r requirements.txt
```

# How to start

1. Plug your favorite RTL-SDR device to your machine.
2. In the `app` directory, call `python decoder.py`

# Credits
Full credits to [F4EHY](http://jgsenlis.free.fr) for the decoding part.
