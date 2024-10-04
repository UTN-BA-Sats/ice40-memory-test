#!/bin/make

# Por defecto suponemos que se va a trabajar con la EDU-FPGA
TARGET=EDUFPGA

# El package y tamaño dependen de la plataforma a utilizar.

# Si se usa la EDU-FPGA
ifeq ($(TARGET),EDUFPGA)
	PACKAGE = tq144
	SIZE = --hx4k
endif

# Si se usa el Lattice iCEstick
ifeq ($(TARGET),ICESTICK)
	PACKAGE = tq144
	SIZE = --hx1k
endif

# Sintetizar
synthesis:
	yosys -p "synth_ice40 -top top -json top.json" $(TOP_LEVEL_FILE)

# Ejecutar Place and Route
pnr:
	nextpnr-ice40 $(SIZE) --package $(PACKAGE) --json top.json --pcf $(PINOUT_FILE) --asc top.asc

# Generar Bitstream
bitstream:
	icepack top.asc top.bin

# Configurar la placa
program:
	iceprog top.bin

# Limpiar subproductos
clean:
	rm -f *.blif
	rm -f *.asc
	rm -f *.bin

# Proceso completo
all: synthesis pnr bitstream program clean
