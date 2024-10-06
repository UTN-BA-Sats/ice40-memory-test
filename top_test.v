`include "../memory_mock.v"
`include "../spi_slave.v"
`include "../address_mapper.v"
`include "../fsm.v"
`include "../signature.v"

module top(
    input clk,
    input i_mosi,
    input i_sck,
    input i_cs,
    input i_rst,
    output o_miso
);

wire srst;

wire rx_data_valid;
wire tx_data_valid;
wire tx_ready;

assign srst = i_rst;

wire [7:0] w_rx_byte;

wire [15:0] w_rx_addr;
wire [7:0] w_data;
wire [20:0] mem_cs_aux;
wire [20:0] mem_cs;
wire mem_byte_sel;
wire [7:0] w_mem_addr;
wire w_addr_valid;

wire [2:0] test_fsm_state;

Address_Mapper address_mapper_inst(
    .i_addr(w_rx_addr),
    .o_ram_cs(mem_cs_aux),
    .o_byte_addr(w_mem_addr),
    .o_bank(mem_byte_sel)
);

FSM fsm_inst(
    .i_cs(i_cs),
    .i_clk(clk),
    .i_rx_byte(w_rx_byte),
    .i_data_valid(rx_data_valid),
    .i_tx_ready(tx_ready),
    .o_rx_addr(w_rx_addr),
    .o_addr_valid(w_addr_valid),
    .o_state_test(test_fsm_state),
    .o_data_valid(tx_data_valid)
);

genvar i;

for(i = 0; i < 20; i = i+1) begin
    assign mem_cs[i] = mem_cs_aux[i] & w_addr_valid;
    Memory memory_inst(
        .clk(clk),
        .reset(srst),
        .addr(w_mem_addr),
        .data_byte(w_data),
        .cs(mem_cs[i]),
        .byte_sel(mem_byte_sel)
    );
end

assign mem_cs[20] = mem_cs_aux[20] & w_addr_valid;

Signature signature_inst(
    .addr({w_mem_addr[0],mem_byte_sel}),
    .cs(mem_cs[20]),
    .data(w_data)
);

SPI_Slave spi_slave(
    .i_rst(srst),
    .i_clk(clk),
    .o_rx_valid(rx_data_valid),
    .o_rx_byte(w_rx_byte),
    .i_tx_valid(tx_data_valid),
    .i_tx_byte(w_data),
    .o_tx_ready(tx_ready),

    .i_sck(i_sck),
    .o_miso(o_miso),
    .i_mosi(i_mosi),
    .i_cs(i_cs)
);

endmodule
