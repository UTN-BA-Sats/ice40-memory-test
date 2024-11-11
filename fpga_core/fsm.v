module FSM(
    input i_cs,
    input i_clk,
    input [7:0] i_rx_byte,
    input i_data_valid,
    input i_tx_ready,
    output reg [15:0] o_rx_addr,
    output reg o_addr_valid,
    output reg o_data_valid,
    output reg [7:0] o_rx_data,
    output reg o_mem_rw
);

localparam START = 4'b0000;
localparam MSB_RECEIVED = 4'b0001;
localparam LSB_RECEIVING = 4'b0010;
localparam LSB_RECEIVED = 4'b0011;
localparam READ_MEM = 4'b0100;
localparam LOAD_SPI = 4'b0101;
localparam SEND = 4'b0110;
localparam DATA_RECEIVING = 4'b0111;
localparam DATA_RECEIVED = 4'b1000;
localparam DATA_STORED = 4'b1001;

reg [3:0] state;
reg [3:0] next_state;

reg [7:0] r_rx_byte;

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
                if(o_rx_addr[15]) begin
                    next_state = DATA_RECEIVING;
                end else begin
                    next_state = READ_MEM;
                end
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

        DATA_RECEIVING: begin
            if(i_data_valid == 1) begin
                next_state = DATA_RECEIVED;
            end else begin
                next_state = DATA_RECEIVING;
            end
        end

        DATA_RECEIVED: begin
            if(i_data_valid == 0) begin
                next_state = DATA_STORED;
            end else begin
                next_state = DATA_RECEIVED;
            end
        end

        DATA_STORED: begin
            next_state = DATA_RECEIVING;
        end

        default: next_state = START;
    endcase
end

always @(posedge i_clk or posedge i_cs) begin
    if(i_cs == 1) begin
        state <= START;
        o_addr_valid <= 0;
        o_data_valid <= 0;
        o_mem_rw <= 0;
        o_rx_addr <= 16'b0;
    end else begin
        state <= next_state;

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

            DATA_RECEIVED: begin
                o_mem_rw <= 1;
                o_rx_data <= r_rx_byte;
            end

            DATA_STORED: begin
                o_mem_rw <= 0;
                o_rx_addr <= o_rx_addr + 1;
            end
        endcase
    end
end

endmodule