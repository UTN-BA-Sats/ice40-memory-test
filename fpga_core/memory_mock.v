module Memory (
    input clk,
    input reset,
    input [8:0] addr,
    input cs,
    input rw,
    input [7:0] i_data_byte,
    output [7:0] o_data_byte
);

reg [7:0] mem[511:0];

reg [7:0] r_data_read;

assign read_en = cs;
assign o_data_byte = cs == 1 ? r_data_read : 8'bz;

initial begin : mem_init
    integer i;
    for(i = 0; i < 256; i = i + 1) begin
        mem[2 * i] = 8'h0A + i;
        mem[2 * i + 1] = 8'h55;
    end
end

always @(posedge clk) begin
    if(reset == 1'b0) begin
        r_data_read <= mem[8'b0];
    end else begin
        r_data_read <= mem[addr];

        if(rw)
            mem[addr] <= i_data_byte;
    end
end

endmodule 
