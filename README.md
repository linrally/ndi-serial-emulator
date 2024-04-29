# NDI Polaris API Serial Emulator
A Python emulator for serial communication with the NDI Polaris Vega optical tracker. Designed for compatibility with the [NDI C API](https://github.com/PlusToolkit/ndicapi/tree/master).

## Usage (MacOS)
Create a virtual serial port using socat.

```
socat -d -d pty,raw,echo=1 pty,raw,echo=1
```

Run `emulator.py`
