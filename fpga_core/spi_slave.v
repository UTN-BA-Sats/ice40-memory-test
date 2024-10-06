module SPI_Slave(
    input i_clk,
    input i_rst,

    input i_cs,
    input i_sck,
    input i_mosi,
    output o_miso,

    input [7:0] i_tx_byte,
    input i_tx_valid,
    output reg [7:0] o_rx_byte,
    output reg o_rx_valid,
    output o_tx_ready
);

reg [2:0] r_sck;
reg [1:0] r_cs;

wire w_cs_falling = r_cs == 2'b10;
wire w_cs_rising = r_cs == 2'b01;
wire w_sck_rising = r_sck[2:1] == 2'b01;
wire w_sck_falling = r_sck[2:1] == 2'b10;

reg [2:0] r_bit_count;
reg [7:0] r_miso_shift;
reg [7:0] r_rx_byte;
reg r_tx_ready;

reg [7:0] r_tx_byte;

assign o_miso = r_miso_shift[7];
assign o_tx_ready = r_tx_ready;

// Synchronization
always @(posedge i_clk, negedge i_rst) begin
    if(i_rst == 0) begin
        r_sck <= 3'b0;
        r_cs <= 2'b11;
    end else begin
        r_sck <= {r_sck[1:0], i_sck};
        r_cs <= {r_cs[0], i_cs};
    end
end

// Rx process
always @(posedge i_clk) begin
    if(r_cs[1] == 1) begin
        r_bit_count <= 3'b0;
        o_rx_valid <= 1'b0;
    end else if(w_sck_rising) begin
        r_bit_count <= r_bit_count + 1;
        o_rx_byte <= {o_rx_byte[6:0], i_mosi};

        if(r_bit_count == 3'b111) begin
            o_rx_valid <= 1;
        end else begin
            o_rx_valid <= 0;
        end
    end
end

// Tx process
always @(posedge i_clk) begin
    if((r_cs[1] == 0 && w_sck_falling) || w_cs_falling) begin
        r_miso_shift <= {r_miso_shift[6:0], 1'b0};

        if(r_tx_ready && i_tx_valid) begin
            r_miso_shift <= r_tx_byte;
        end
    end
end

// When is it possible to update the Tx byte
always @(posedge i_clk) begin
    if((w_sck_rising && r_bit_count == 3'b111) || r_cs[1] == 1) begin
        r_tx_ready <= 1;
    end else if(r_bit_count == 3'b000 && (w_sck_falling || w_cs_falling)) begin
        r_tx_ready <= 0;
    end

    r_tx_byte <= i_tx_byte;
end

endmodule