module FSM(
    input i_cs,
    input i_clk,
    input [7:0] i_rx_byte,
    input i_data_valid,
    input i_tx_ready,
    output reg [15:0] o_rx_addr,
    output reg o_addr_valid,
    output reg o_data_valid,
    output [2:0] o_state_test
);

localparam START = 3'b000;
localparam MSB_RECEIVED = 3'b001;
localparam LSB_RECEIVING = 3'b010;
localparam LSB_RECEIVED = 3'b011;
localparam READ_MEM = 3'b100;
localparam LOAD_SPI = 3'b101;
localparam SEND = 3'b110;

reg [2:0] state;
reg [2:0] next_state;

reg prev_tx_ready;

reg [7:0] r_rx_byte;

assign o_state_test = state;

always @(*) begin
    case(state)
        START: begin
            if(i_data_valid == 1) begin
                next_state = MSB_RECEIVED;
            end else begin
                next_state = START;
            end
        end
        
        MSB_RECEIVED: begin
            if(i_data_valid == 0) begin
                next_state = LSB_RECEIVING;
            end else begin
                next_state = MSB_RECEIVED;
            end
        end

        LSB_RECEIVING: begin
            if(i_data_valid == 1) begin
                next_state = LSB_RECEIVED;
            end else begin
                next_state = LSB_RECEIVING;
            end
        end

        LSB_RECEIVED: begin
            if(i_data_valid == 0) begin
                next_state = READ_MEM;
            end else begin
                next_state = LSB_RECEIVED;
            end
        end

        READ_MEM: begin
            if(i_tx_ready == 1) begin
                next_state = LOAD_SPI;
            end else begin
                next_state = READ_MEM;
            end
        end

        LOAD_SPI: begin
            if(i_tx_ready == 0) begin
                next_state = SEND;
            end else begin
                next_state = LOAD_SPI;
            end
        end

        SEND: begin
            next_state = READ_MEM;
        end

        default: next_state = START;
    endcase
end

always @(posedge i_clk or posedge i_cs) begin
    if(i_cs == 1) begin
        state <= START;
        o_addr_valid <= 0;
        o_data_valid <= 0;
        o_rx_addr <= 16'b0;
        prev_tx_ready <= 0;
    end else begin
        state <= next_state;
        prev_tx_ready <= i_tx_ready;

        if(i_data_valid) begin
            r_rx_byte <= i_rx_byte;
        end

        case(state)
            MSB_RECEIVED: begin
                o_rx_addr[15:8] <= r_rx_byte;
            end

            LSB_RECEIVED: begin
                o_rx_addr[7:0] <= r_rx_byte;
                o_addr_valid <= 1;
            end

            READ_MEM: begin
                o_data_valid <= 1;
            end

            SEND: begin
                o_data_valid <= 0;
                o_rx_addr <= o_rx_addr + 1;
            end
        endcase
    end
end

endmodule