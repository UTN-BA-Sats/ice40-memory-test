module Signature(
    input [1:0] addr,
    input cs,
    output [7:0] data
);

reg [7:0] data_byte;

assign data = cs == 1 ? data_byte : 8'bz;

always @(*) begin
    case(addr)
        2'd0: data_byte = 8'h2b;
        2'd1: data_byte = 8'ha7;
        2'd2: data_byte = 8'h56;
        2'd3: data_byte = 8'h8b;
        default data_byte = 'bx;
    endcase
end

endmodule