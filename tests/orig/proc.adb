with Ada.Text_IO; use Ada.Text_IO;
with P; use P;

procedure proc is
   
   procedure A is
   begin
      B;
   end A;
   
   procedure C is
      procedure Nested is
      begin
         null;
      end;
   begin
      A;
   end C;
      
begin
   A;
   B;
   C;
   Put_Line ("bye");
   Put_Line ("bye");
   Put_Line ("bye");
end proc;
