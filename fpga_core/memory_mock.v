module Memory (
    input clk,
    input reset,
    input [7:0] addr,
    input cs,
    input read_byte_sel,
    input rw,
    input [15:0] i_data_word,
    output [7:0] o_data_byte
);

reg [15:0] mem[255:0];

reg [15:0] r_data_read;

assign read_en = cs;
assign o_data_byte = cs == 1 ? (read_byte_sel == 1 ? r_data_read[15:8] : r_data_read[7:0]) : 8'bz;

initial begin : mem_init
    integer i;
    for(i = 0; i < 256; i = i + 1) begin
        mem[i] = 16'h550A + i;
    end
end

always @(posedge clk) begin
    if(reset == 1'b0) begin
        r_data_read <= mem[16'b0];
    end else begin
        r_data_read <= mem[addr];

        if(rw)
            mem[addr] <= i_data_word;
    end
end

endmodule 
