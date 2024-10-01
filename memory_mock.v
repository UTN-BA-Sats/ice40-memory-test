module Memory (
    input clk,
    input reset,
    input [7:0] addr,
    input cs,
    input byte_sel,
    output [7:0] data_byte
);

reg [15:0] mem[255:0];

reg [15:0] r_data;

assign read_en = cs;
assign data_byte = cs == 1 ? (byte_sel == 1 ? r_data[15:8] : r_data[7:0]) : 8'bz;

initial begin : mem_init
    integer i;
    for(i = 0; i < 256; i = i + 1)
        mem[i] = 16'h000A + i;
end

always @(posedge clk) begin
    if(reset == 1'b0) begin
        r_data <= mem[8'b0];
    end else begin
        r_data <= mem[addr];
    end
end

endmodule 
