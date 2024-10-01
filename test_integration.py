import os
import sys
import subprocess
import random
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.runner import get_runner
from cocotb.triggers import Timer
from cocotb.triggers import RisingEdge
from cocotb.triggers import ClockCycles
from cocotb.triggers import ReadOnly
from cocotb.triggers import ReadWrite
from cocotb.triggers import NextTimeStep

#do not change
COCOTB_HDL_TIMEUNIT = "1ns"
COCOTB_HDL_TIMEPRECISION = "1ps"
IGNORED_SRC_FOLDERS = ["__pycache__", "sim_build"]

DUT = "top"

@cocotb.test()
async def integration_test(dut):
    SPI_PERIOD = 100

    addr_low = 0x00
    addr_high = 0x00

    clkTask = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clkTask.start())

    dut.i_rst = 0
    dut.i_sck = 0
    dut.i_cs = 1
    dut.i_mosi = 0

    # Reset and initial values
    for i in range(5):
        await RisingEdge(dut.clk)

    dut.i_rst = 1

    dut.i_cs = 0
    dut.i_mosi = (addr_high >> 7) & 0x01

    for bit in range(6, -1, -1):
        await Timer(SPI_PERIOD/2, units="ns")
        dut.i_sck = 1
        await Timer(SPI_PERIOD/2, units="ns")
        dut.i_sck = 0
        dut.i_mosi = (addr_high >> bit) & 0x01

    await Timer(SPI_PERIOD/2, units="ns")
    dut.i_sck = 1
    await Timer(SPI_PERIOD/2, units="ns")
    dut.i_sck = 0
    dut.i_mosi = (addr_low >> 7) & 0x01

    for bit in range(6, -1, -1):
        await Timer(SPI_PERIOD/2, units="ns")
        dut.i_sck = 1
        await Timer(SPI_PERIOD/2, units="ns")
        dut.i_sck = 0
        dut.i_mosi = (addr_low >> bit) & 0x01

    await Timer(SPI_PERIOD/2, units="ns")
    dut.i_sck = 1
    await Timer(SPI_PERIOD/2, units="ns")

    for addr in range(5):
        dut.i_sck = 0

        rx_data = 0
        for bit in range(7, -1, -1):
            dut.i_sck = 0
            await Timer(SPI_PERIOD/2, units="ns")
            dut.i_sck = 1
            rx_data |= int(dut.o_miso) << bit
            await Timer(SPI_PERIOD/2, units="ns")

        print("data from memory = ", hex(rx_data))

    dut.i_sck = 0
    dut_i_cs = 1

def test_simple_dff_runner():

    sim = os.getenv("SIM", "icarus")

    proj_path = Path(__file__).resolve().parent

    sources = []

    # create directory for simulated waveform
    try:
        os.mkdir(os.path.join(proj_path, "sim_build"))
    except FileExistsError:
        print("Not pre-creating sim_build directory because it exists")

    # create command file to establish iverilog timesteps
    # cocotb defaults to timescale 1ns, timeprecision 1ps
    cmdfile_path = os.path.join(proj_path, "sim_build", "icarus_cmd.f")
    cmdfile = open(cmdfile_path, "w")
    cmdfile.write(f"+timescale+{COCOTB_HDL_TIMEUNIT}/{COCOTB_HDL_TIMEPRECISION})\n")
    cmdfile.close()

    #create extra verilog file to enable waveforms
    #same as done in Makefile.icarus from cocotb repo
    wavever_path = os.path.join(proj_path, "sim_build", "cocotb_icarus_dump.v")
    waveverfile = open(wavever_path, "w")
    waveverfile.write("module cocotb_icarus_dump();\n")
    waveverfile.write("initial begin\n")
    waveverfile.write(f"$dumpfile(\"{proj_path}/sim_build/waveform.vcd\");\n")
    waveverfile.write(f"$dumpvars(0, {DUT});\n")
    waveverfile.write("end\n")
    waveverfile.write("endmodule\n")
    waveverfile.close()

    #locate all verilog sources
    for path, subdirs, files in os.walk(proj_path):
        dirname = os.path.basename(os.path.normpath(path))
        if (dirname in IGNORED_SRC_FOLDERS):
            print(f"Ignoring folder {dirname}")
            continue
        for name in files:
            if name.endswith("top_test.v"):
                sourcePath = os.path.join(path, name)
                print("Adding source: " + sourcePath)
                sources.append(os.path.relpath(sourcePath, proj_path))

    #include verilog to dump waveforms
    sources.append(os.path.join("./", "sim_build", "cocotb_icarus_dump.v"))

    runner = get_runner(sim)()
    runner.build(
        verilog_sources=sources,
        toplevel=DUT,
        extra_args=["-f", cmdfile_path],
    )

    try:
        runner.test(
            toplevel=DUT, 
            py_module="test_integration"
            )
    except:
        pass
    
    if (sys.argv[1] == "--wave"):
        print("Calling gtkwave to view waveform...\n")
        wavefile = os.path.join(proj_path, "sim_build", "waveform.vcd")
        if (os.path.exists(wavefile)):
            prog = ["gtkwave", str(os.path.relpath(wavefile, proj_path))]
            subprocess.run(prog)
    


if __name__ == "__main__":
    test_simple_dff_runner()