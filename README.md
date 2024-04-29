# NDI Polaris API Serial Emulator
A Python emulator for serial communication with the NDI Polaris Vega optical tracker designed for the [Brain Stimulation Engineering Lab](https://sites.google.com/view/bsel/) at Duke University. Compatible with the [NDI C API](https://github.com/PlusToolkit/ndicapi/tree/master).

## Usage (MacOS)
Clone the git repository.
```
git clone https://github.com/linrally/ndi-serial-emulator.git
```

Create a virtual serial port using socat.

```
socat -d -d pty,raw,echo=1 pty,raw,echo=1
```

Run `emulator.py`
