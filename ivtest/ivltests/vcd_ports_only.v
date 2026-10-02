// Check that -vcd-ports-only dumps only the ports of each module.
module inv(input i, output o);
   assign o = ~i;
endmodule

module blk(input a, output y);
   wire n;
   inv g(.i(a), .o(n));
   assign y = ~n;
endmodule

module main;
   reg a;
   wire y;
   reg [8*64:1] line;
   integer fd;
   blk u1(.a(a), .y(y));

   initial begin
      $dumpfile("work/vcd_ports_only.vcd");
      $dumpvars(0, main);
      a = 0;
      #1 a = 1;
      #1 $dumpflush;
      // Print the dump back so the gold file records which signals were dumped
      fd = $fopen("work/vcd_ports_only.vcd", "r");
      while ($fgets(line, fd)) $write("%0s", line);
      $fclose(fd);
   end
endmodule
