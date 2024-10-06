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


DUT = "SPI_Slave"

@cocotb.test()
async def mosi_and_miso(dut):
    clkTask = Clock(dut.i_clk, 10, units="ns")
    cocotb.start_soon(clkTask.start())

    dut.i_rst = 0
    dut.i_tx_valid = 0
    dut.i_sck = 0
    dut.i_mosi = 0
    dut.i_cs = 1

    await Timer(6, units="ns")
    dut.i_rst = 1
    await Timer(10, units="ns")

    assert 1 == dut.o_tx_ready;

    tx_data = 0x55

    dut.i_cs = 0
    dut.i_mosi = (tx_data >> 7) & 0x01

    for bit in range(6, -1, -1):
        await Timer(50, units="ns")
        dut.i_sck = 1
        await Timer(50, units="ns")
        dut.i_sck = 0
        dut.i_mosi = (tx_data >> bit) & 0x01

    await Timer(50, units="ns")
    dut.i_sck = 1

    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)
    await ReadOnly()

    assert 1 == dut.o_rx_valid
    assert tx_data == dut.o_rx_byte

    assert 1 == dut.o_tx_ready;

    await RisingEdge(dut.i_clk)

    dut.i_tx_byte = 0x27
    dut.i_tx_valid = 1

    await Timer(50 - 3 * 10, units="ns")

    rx_data = 0
    for bit in range(7, -1, -1):
        dut.i_sck = 0
        await Timer(50, units="ns")
        dut.i_sck = 1
        rx_data |= int(dut.o_miso) << bit
        await Timer(50, units="ns")

    assert 0x27 == rx_data

    dut.i_sck = 0
    dut.i_cs = 1

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
            if name.endswith("spi_slave.v"):
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
            py_module="test_spi_slave"
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
