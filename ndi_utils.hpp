#pragma once

#include <iostream>
#include <vector>
#include <algorithm>
#include <future>
#include <array>
#include <fstream>
#include <sstream>
#include <filesystem>

#include <ndicapi.h>

#define ROM_ADDR_NUM_MARKERS 28
#define ROM_ADDR_MARKER_XYZ_BEGIN 72 

// This implementation creates tasks and continuously polls each one
std::string ParallelProbe(bool checkDSR, int maxPortNum, std::vector<std::future<std::string>>& probeTasks)
{
  probeTasks.clear();
  for (int i = 0; i < maxPortNum; i++)
  {
    // get serial port #i's full name (e.g., "COM*" on Windows, "/dev/cu.usbserial-******" on macOS)
    const char* portName = ndiSerialDeviceName(i);
    if (portName != nullptr)
    {
      std::string portNameStr(portName); // use std::string instead of raw char* for lambda copy capture
      // check if device at port #i is an NDI camera; return its full name if so, otherwise return an empty string
      probeTasks.push_back(std::move(std::async(std::launch::async, [portNameStr, checkDSR]()
        {
          return ndiSerialProbe(portNameStr.c_str(), checkDSR) == NDI_OKAY ? portNameStr : std::string();
        }
      )));
    }
  }
  int numTasksReady = 0;
  while (numTasksReady < probeTasks.size())
  {
    // iterate over each task
    for (auto& probeTask : probeTasks)
    {
      // check if task has completed
      if (probeTask.valid() && probeTask.wait_for(std::chrono::seconds(0)) == std::future_status::ready)
      {
        // if the serial port contains a valid NDI camera, immediately open and return it
        std::string portName = probeTask.get();
        if (!portName.empty())
        {
          return portName;
        }
        numTasksReady++;
      }
    }
  }
  return std::string();
}

std::vector<std::array<float, 3>> parseROM(const char* romdata){
  int numMarkers = romdata[ROM_ADDR_NUM_MARKERS];
  std::vector<std::array<float, 3>> markers;
  for (int i = 0; i < numMarkers; i++){
    std::array<float, 3> marker_arr;
    unsigned int pos = ROM_ADDR_MARKER_XYZ_BEGIN + i*12;
    memcpy(marker_arr.data(), &romdata[pos], 12);
    markers.push_back(marker_arr);
  }
  return markers;
}

bool initNDIDevice(std::unique_ptr<ndicapi, decltype(&ndiCloseSerial)>& device, std::string& devicePort, std::string& firmwareString){
  device.reset(ndiOpenSerial(devicePort.c_str()));

  const char* reply = ndiINIT(device.get());
  if (strncmp(reply, "ERROR", strlen(reply)) == 0 || ndiGetError(device.get()) != NDI_OKAY){
      std::cerr << "Error when sending command: " << ndiErrorString(ndiGetError(device.get())) << std::endl;
      return false;
  }

  reply = ndiCommand(device.get(), "COMM:%d%03d%d", NDI_115200, NDI_8N1, NDI_NOHANDSHAKE);
  firmwareString.assign(ndiVER(device.get(), 0));
  return true;
}

bool initROMFiles(
  std::unique_ptr<ndicapi, decltype(&ndiCloseSerial)>& device,
  const std::vector<std::filesystem::path>& rom_files,
  std::vector<int>& tracker_ports,
  std::vector<std::vector<std::array<float, 3>>>& marker_data
){
  // Free stale handles
  ndiPHSR(device.get(), NDI_STALE_HANDLES);
  for (int i = 0; i < ndiGetPHSRNumberOfHandles(device.get()); i++){
    ndiPHF(device.get(), ndiGetPHSRHandle(device.get(), i));
  }

  tracker_ports.clear();
  marker_data.clear();
  for (int i = 0; i < rom_files.size(); i++){
    const auto& abspath = std::filesystem::absolute(rom_files[i]);

    // Set up new handle
    ndiPHRQ(device.get(), "********", "*", "1", "**", "**"); // get a port for a new wireless tool
    const int port = ndiGetPHRQHandle(device.get());
    tracker_ports.push_back(port);

    std::ifstream f(abspath);
    if (f.fail()){
      std::cout << "ROM file " << abspath.string() << " not found!" << std::endl;
      return false;
    }
    std::stringstream buffer;
    buffer << f.rdbuf();

    if (buffer.str().size() > 1024){
      throw std::length_error("Input ROM file exceeds maximum of 1024 bytes!");
    }

    // write 1024 bytes in chunks of 64
    device->ErrorCode = 0;
    char hexdata[128];
    for (int addr = 0; addr < buffer.str().size(); addr += 64){
      ndiPVWR(device.get(), port, addr, ndiHexEncode(hexdata, &buffer.str()[addr], 64));
      if (ndiGetError(device.get()) != NDI_OKAY) return false;
    }

    marker_data.push_back(parseROM(buffer.str().data()));
  }
  
  // Initialize all tools
  ndiPHSR(device.get(), NDI_UNINITIALIZED_HANDLES);
  for (int i = 0; i < ndiGetPHSRNumberOfHandles(device.get()); i++){
    ndiPINIT(device.get(), ndiGetPHSRHandle(device.get(), i));
  }

  // Enable all tools
  ndiPHSR(device.get(), NDI_UNENABLED_HANDLES);
  for (int i = 0; i < ndiGetPHSRNumberOfHandles(device.get()); i++){
    ndiPENA(device.get(), ndiGetPHSRHandle(device.get(), i), NDI_DYNAMIC);
  }
  return true;
}