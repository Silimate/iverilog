// Check that -udp-init-zero sets each sequential UDP whose x is stored state
// to 0 once time 0 settles, also one clocked by another, without the clear
// clocking it; leaves an open latch to its input, so a latch fed by its own
// inverse stays x instead of oscillating, while level changes still apply;
// clears a flop whose level rows only hold a stored value; and leaves known
// outputs and combinational UDPs alone.

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

// Loads d on a clock rising from x as well as from 0.
primitive dff_x1 (q, d, clk);
   output q;
   reg q;
   input d, clk;
   table
   // d  clk  : q : q+
      0  (?1) : ? : 0;
      1  (?1) : ? : 1;
      ?  (?0) : ? : -;
      *  ?    : ? : -;
   endtable
endprimitive

// Its level rows only keep a stored 0 or 1 while the clock is low, so they
// do not decide an x output, even while d is x.
primitive dff_hold (q, d, clk);
   output q;
   reg q;
   input d, clk;
   table
   // d  clk  : q : q+
      0  (01) : ? : 0;
      1  (01) : ? : 1;
      0  0    : 0 : 0;
      1  0    : 1 : 1;
      ?  (?0) : ? : -;
      *  ?    : ? : -;
   endtable
endprimitive

primitive latch (q, d, en);
   output q;
   reg q;
   input d, en;
   table
   // d  en : q : q+
      0  1  : ? : 0;
      1  1  : ? : 1;
      ?  0  : ? : -;
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

// Known only for an x or 1 input, so u0 being cleared to 0 sends it to x.
primitive xone (o, i);
   output o;
   input i;
   table
      x : 1;
      1 : 0;
   endtable
endprimitive

module main;
   reg d, clk, dl, dl2;
   wire q, q1, b, qb, q2, qn, ql, clkn, q5, c, q6, qr, qrn, ql7, ql8, qh;

   dff u0 (q, d, clk);
   dff_init1 u1 (q1, d, clk);
   buf_udp u2 (b, d);
   // Clocked by u0, so u0 going from x to 0 is an x->0 clock it has no row for.
   buf (qb, q);
   dff u3 (q2, d, qb);
   // Open, so left at x, then it follows u0 being cleared to 0.
   not (qn, q);
   latch u4 (ql, qn, 1'b1);
   // Known before time 0 settles, sent to x by the time 0 clock: cleared to 0.
   not (clkn, clk);
   dff_init1 u5 (q5, d, clkn);
   // Combinational, so u0 being cleared to 0 still sends it to x.
   xone u6 (c, q);
   // Clocked by qn rising from x when u0 is cleared: the clear is no clock edge.
   dff_x1 u7 (q6, 1'b1, qn);
   // An open latch fed by its own inverse stays x.
   not (qrn, qr);
   latch u8 (qr, qrn, 1'b1);
   // An x at time 1 is honoured.
   latch u9 (ql7, dl, 1'b1);
   // Open and known, with its input set by a process u0 being cleared wakes:
   // a level change still applies within time 0.
   latch u10 (ql8, dl2, 1'b1);
   always @(negedge q) dl2 = 1;
   // Its hold rows do not keep it at x.
   dff_hold u11 (qh, d, clk);

   initial begin
      clk = 0;
      dl = 0;
      dl2 = 0;
      #1 $display("before: q=%b q1=%b b=%b q2=%b ql=%b q5=%b c=%b q6=%b qr=%b ql8=%b qh=%b",
                  q, q1, b, q2, ql, q5, c, q6, qr, ql8, qh);
      d = 1;
      dl = 1'bx;
      #1 clk = 1;
      #1 $display("after: q=%b q1=%b b=%b q2=%b ql=%b ql7=%b qh=%b",
                  q, q1, b, q2, ql, ql7, qh);
      // After time 0 an x is honoured again.
      d = 1'bx;
      clk = 0;
      #1 clk = 1;
      #1 $display("x after time 0: q=%b", q);
   end
endmodule
