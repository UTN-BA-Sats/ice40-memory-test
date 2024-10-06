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


DUT = "Signature"

@cocotb.test()
async def check_signature_rom(dut):
    expected_data = [0x2b, 0xa7, 0x56, 0x8b]

    addr = 0
    for e in expected_data:
        dut.addr = addr
        dut.cs = 1
        await Timer(1, units="ns")
        assert e == dut.data
        addr += 1

    dut.cs = 0
    await Timer(1, units="ns")
    assert 'zzzzzzzz' == dut.data.value.binstr

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
            if name.endswith("signature.v"):
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
            py_module="test_signature"
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
