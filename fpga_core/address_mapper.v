module Address_Mapper(
    input [15:0] i_addr,
    output [20:0] o_ram_cs,
    output [8:0] o_byte_addr
);

assign o_byte_addr = i_addr[8:0];

assign o_ram_cs = 1 << i_addr[13:9];

endmodule