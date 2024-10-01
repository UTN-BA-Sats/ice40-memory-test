module Address_Mapper(
    input [15:0] i_addr,
    output [19:0] o_ram_cs,
    output [7:0] o_byte_addr,
    output o_bank
);

assign o_byte_addr = i_addr[8:1];
assign o_bank = i_addr[0];

assign o_ram_cs = 1 << i_addr[13:9];

endmodule