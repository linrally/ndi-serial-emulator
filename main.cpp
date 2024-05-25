#include <cstring>
#include <iostream>

#include <ndicapi.h>

#include "ndi_utils.hpp"

using namespace std;

bool checkDSR = false; // Currently unused; needs implementation?
std::string ndi_port("/dev/ttys020");
std::string ndi_firmware_str;
std::unique_ptr<ndicapi, decltype(&ndiCloseSerial)> ndi_device(nullptr, ndiCloseSerial);

const std::vector<std::filesystem::path> ROM_FILES = {"ROMs/ST1257.rom", "ROMs/P1520.rom","ROMs/LCT576.rom"}; // 0 - subject tracker; 1 - pointer; 2 - stationary pointer
std::vector<int> tracker_ports;
std::vector<std::vector<std::array<float, 3>>> marker_data;

int main(int argc, char *argv[])
{
    cout << initNDIDevice(ndi_device, ndi_port, ndi_firmware_str) << endl;

    cout << initROMFiles(ndi_device, ROM_FILES, tracker_ports, marker_data) << endl;

    return EXIT_SUCCESS;
}