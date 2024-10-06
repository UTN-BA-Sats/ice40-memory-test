module Memory
#(parameter INIT_0 = 256'h0, 
   parameter INIT_1 = 256'h0,
   parameter INIT_2 = 256'h0,
   parameter INIT_3 = 256'h0,
   parameter INIT_4 = 256'h0,
   parameter INIT_5 = 256'h0,
   parameter INIT_6 = 256'h0,
   parameter INIT_7 = 256'h0,
   parameter INIT_8 = 256'h0,
   parameter INIT_9 = 256'h0,
   parameter INIT_A = 256'h0,
   parameter INIT_B = 256'h0,
   parameter INIT_C = 256'h0,
   parameter INIT_D = 256'h0,
   parameter INIT_E = 256'h0,
   parameter INIT_F = 256'h0
)
(
    input clk,
    input reset,
    input [7:0] addr,
    input cs,
    input byte_sel,
    // output [15:0] data,
    output [7:0] data_byte
);

SB_RAM40_4K ram256x16_inst (
    .RDATA(r_data),
    .RADDR(r_addr),
    .RCLK(clk),
    .RCLKE(clk_en),
    .RE(read_en),
    .WADDR(w_addr),
    .WCLK(clk),
    .WCLKE(clk_en),
    .WDATA(w_data),
    .WE(write_en),
    .MASK(mask)
);

defparam ram256x16_inst.READ_MODE = 0;
defparam ram256x16_inst.WRITE_MODE = 0;

defparam ram256x16_inst.INIT_0 = INIT_0;
defparam ram256x16_inst.INIT_1 = INIT_1;
defparam ram256x16_inst.INIT_2 = INIT_2;
defparam ram256x16_inst.INIT_3 = INIT_3;
defparam ram256x16_inst.INIT_4 = INIT_4;
defparam ram256x16_inst.INIT_5 = INIT_5;
defparam ram256x16_inst.INIT_6 = INIT_6;
defparam ram256x16_inst.INIT_7 = INIT_7;
defparam ram256x16_inst.INIT_8 = INIT_8;
defparam ram256x16_inst.INIT_9 = INIT_9;
defparam ram256x16_inst.INIT_A = INIT_A;
defparam ram256x16_inst.INIT_B = INIT_B;
defparam ram256x16_inst.INIT_C = INIT_C;
defparam ram256x16_inst.INIT_D = INIT_D;
defparam ram256x16_inst.INIT_E = INIT_E;
defparam ram256x16_inst.INIT_F = INIT_F;

wire [10:0] r_addr;
wire [10:0] w_addr;
wire[15:0] r_data;
wire[15:0] w_data;
wire read_en;
wire write_en;
wire clk_en;
wire [15:0] mask;

assign read_en = cs;
// assign data = r_data;
assign data_byte = cs == 1 ? (byte_sel == 1 ? r_data[15:8] : r_data[7:0]) : 8'bz;
// assign data_byte = byte_sel == 1 ? r_data[15:8] : r_data[7:0];

assign clk_en = 1;
assign write_en = 0;
assign r_addr = {3'b0, addr};
assign w_addr = 11'b0;
assign w_data = 16'b0;
assign mask = 16'b0;

endmodule