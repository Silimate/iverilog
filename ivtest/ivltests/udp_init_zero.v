// Check that -udp-init-zero sets each sequential UDP still at x once time 0
// settles to 0, also one clocked by another, and leaves known outputs and
// combinational UDPs alone.

// No row for a clock falling from x: the x->0 clock at time 0 sets q to x.
primitive dff (q, d, clk);
   output q;
   reg q;
   input d, clk;
   table
   // d  clk  : q : q+
      0  (01) : ? : 0;
      1  (01) : ? : 1;
      ?  (10) : ? : -;
      *  ?    : ? : -;
   endtable
endprimitive

// Holds its initial 1 through the x->0 clock at time 0.
primitive dff_init1 (q, d, clk);
   output q;
   reg q;
   input d, clk;
   initial q = 1'b1;
   table
   // d  clk  : q : q+
      0  (01) : ? : 0;
      1  (01) : ? : 1;
      ?  (?0) : ? : -;
      *  ?    : ? : -;
   endtable
endprimitive

primitive buf_udp (o, i);
   output o;
   input i;
   table
      0 : 0;
      1 : 1;
   endtable
endprimitive

module main;
   reg d, clk;
   wire q, q1, b, qb, q2;

   dff u0 (q, d, clk);
   dff_init1 u1 (q1, d, clk);
   buf_udp u2 (b, d);
   // Clocked by u0, so u0 going from x to 0 is an x->0 clock it has no row for.
   buf (qb, q);
   dff u3 (q2, d, qb);

   initial begin
      clk = 0;
      #1 $display("before clock: q=%b q1=%b b=%b q2=%b", q, q1, b, q2);
      d = 1;
      #1 clk = 1;
      #1 $display("after clock: q=%b q1=%b b=%b q2=%b", q, q1, b, q2);
      // After time 0 an x is honoured again.
      d = 1'bx;
      clk = 0;
      #1 clk = 1;
      #1 $display("x after time 0: q=%b", q);
   end
endmodule
