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


DUT = "FSM"

@cocotb.test()
async def state_machine_read_mem(dut):
    clkTask = Clock(dut.i_clk, 10, units="ns")
    cocotb.start_soon(clkTask.start())

    dut.i_cs = 1;
    dut.i_rx_byte = 0;
    dut.i_data_valid = 0;
    dut.i_tx_ready = 0;

    # Reset and initial values
    for i in range(5):
        await RisingEdge(dut.i_clk)

    dut.i_cs = 0;

    for i in range(8):
        await RisingEdge(dut.i_clk)

    assert 0 == dut.o_addr_valid
    assert 0 == dut.o_mem_rw

    dut.i_rx_byte = 0x55
    dut.i_data_valid = 1
    await RisingEdge(dut.i_clk)
    dut.i_data_valid = 0
    await RisingEdge(dut.i_clk)

    assert 0 == dut.o_addr_valid
    assert 0 == dut.o_mem_rw

    for i in range(14):
        await RisingEdge(dut.i_clk)

    assert 0 == dut.o_addr_valid
    assert 0 == dut.o_mem_rw

    dut.i_rx_byte = 0xAA
    dut.i_data_valid = 1
    await RisingEdge(dut.i_clk)
    dut.i_data_valid = 0
    await RisingEdge(dut.i_clk)

    # LSB_RECEIVING -> LSB_RECEIVED

    await RisingEdge(dut.i_clk)
    await ReadOnly()

    # data stored to o_rx_addr and o_addr_valid set to 1
    # LSB_RECEIVED -> READ_MEM

    assert 1 == dut.o_addr_valid
    assert 0x55AA == dut.o_rx_addr

    await RisingEdge(dut.i_clk)
    await ReadOnly()

    assert 1 == dut.o_data_valid
    assert 0 == dut.o_mem_rw

    for i in range(10):
        await RisingEdge(dut.i_clk)

    dut.i_tx_ready = 1

    await RisingEdge(dut.i_clk)

    # READ_MEM -> LOAD_SPI

    dut.i_tx_ready = 0

    await RisingEdge(dut.i_clk)

    # LOAD_SPI -> SEND

    await RisingEdge(dut.i_clk)
    await ReadOnly()

    # SEND -> READ_MEM
    # o_rx_addr <= o_rx_addr + 1

    assert 0 == dut.o_data_valid
    assert 0 == dut.o_mem_rw
    assert 0x55AB == dut.o_rx_addr

@cocotb.test()
async def state_machine_write_mem(dut):
    clkTask = Clock(dut.i_clk, 10, units="ns")
    cocotb.start_soon(clkTask.start())

    dut.i_cs = 1;
    dut.i_rx_byte = 0;
    dut.i_data_valid = 0;
    dut.i_tx_ready = 0;

    # Reset and initial values
    for i in range(5):
        await RisingEdge(dut.i_clk)

    dut.i_cs = 0;

    for i in range(8):
        await RisingEdge(dut.i_clk)

    assert 0 == dut.o_addr_valid
    assert 0 == dut.o_mem_rw

    dut.i_rx_byte = 0xAA
    dut.i_data_valid = 1
    await RisingEdge(dut.i_clk)
    dut.i_data_valid = 0
    await RisingEdge(dut.i_clk)

    assert 0 == dut.o_addr_valid
    assert 0 == dut.o_mem_rw

    for i in range(14):
        await RisingEdge(dut.i_clk)

    assert 0 == dut.o_addr_valid
    assert 0 == dut.o_mem_rw

    dut.i_rx_byte = 0x55
    dut.i_data_valid = 1
    await RisingEdge(dut.i_clk)
    dut.i_data_valid = 0
    await RisingEdge(dut.i_clk)

    # LSB_RECEIVING -> LSB_RECEIVED

    await RisingEdge(dut.i_clk)
    await ReadOnly()

    # data stored to o_rx_addr and o_addr_valid set to 1
    # LSB_RECEIVED -> DATA_RECEIVING

    assert 1 == dut.o_addr_valid
    assert 0xAA55 == dut.o_rx_addr

    await RisingEdge(dut.i_clk)
    dut.i_rx_byte = 0x46
    dut.i_data_valid = 1

    await RisingEdge(dut.i_clk)
    # DATA_RECEIVING -> DATA_RECEIVED

    dut.i_data_valid = 0

    await RisingEdge(dut.i_clk)
    await ReadOnly()

    assert 0 == dut.o_data_valid
    assert 1 == dut.o_mem_rw
    assert 0x46 == dut.o_rx_data

    # DATA_RECEIVED -> DATA_STORED

    await RisingEdge(dut.i_clk)
    await ReadOnly()

    # DATA_STORED -> DATA_RECEIVING
    assert 0 == dut.o_data_valid
    assert 0 == dut.o_mem_rw
    assert 0xAA56 == dut.o_rx_addr

    for i in range(10):
        await RisingEdge(dut.i_clk)

    dut.i_rx_byte = 0xCD
    dut.i_data_valid = 1
    await RisingEdge(dut.i_clk)

    # DATA_RECEIVING -> DATA_RECEIVED

    dut.i_data_valid = 0

    await RisingEdge(dut.i_clk)
    await ReadOnly()

    assert 0 == dut.o_data_valid
    assert 1 == dut.o_mem_rw
    assert 0xCD == dut.o_rx_data


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
            if name.endswith("fsm.v"):
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
            py_module="test_fsm"
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
