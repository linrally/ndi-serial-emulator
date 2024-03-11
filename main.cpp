#include <ndicapi.h>
#include <cstring>
#include <iostream>

struct ndicapi;

int main(int argc, char *argv[])
{
    bool checkDSR = false;
    ndicapi *device(nullptr);
    const char *name(nullptr);

    if (argc > 1)
        name = argv[1];
    else
    {
        const int MAX_SERIAL_PORTS = 20;
        for (int i = 0; i < MAX_SERIAL_PORTS; ++i)
        {
            name = ndiSerialDeviceName(i);
            int result = ndiSerialProbe(name, checkDSR);
            if (result == NDI_OKAY)
            {
                break;
            }
        }
    }

    if (name != nullptr)
    {
        device = ndiOpenSerial(name);
    }

    if (device != nullptr)
    {
        const char *reply = ndiCommand(device, "INIT:");
        if (strncmp(reply, "ERROR", strlen(reply)) == 0 || ndiGetError(device) != NDI_OKAY)
        {
            std::cerr << "Error when sending command: " << ndiErrorString(ndiGetError(device)) << std::endl;
            return EXIT_FAILURE;
        }

        reply = ndiCommand(device, "COMM:%d%03d%d", NDI_115200, NDI_8N1, NDI_NOHANDSHAKE);

        // Add your own commands here!!!

        ndiCloseSerial(device);
    }

    return EXIT_SUCCESS;
}