# Memory test core
## Prerequisites
* cocotb v1.7.2
* yosys
* nextpnr

## Usage
* Running integration test: `python test_integration.py`
* Uploading core to FPGA: `make TOP_LEVEL_FILE=top.v PINOUT_FILE=pins.pcf all`
