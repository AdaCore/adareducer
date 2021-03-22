with Ada.Text_IO; use Ada.Text_IO;
with P; use P;

procedure proc is
   
   procedure A;

   procedure Nested;

   procedure A is
   begin
      Put_Line ("bye");
   end A;
   
   procedure Nested is
      A : Integer := 42;
      B : Integer := 42;
      C : Integer := 42;
   begin
      null;
   end Nested;

   procedure C is
      procedure Nested;

      procedure Nested is
         procedure A is
            C : Integer := 42;
            D : Integer := 42;
         begin
            B;
         end A;

         procedure B is
            B : Integer := 42;
            C : Integer := 42;
         begin
            A;
         end B;

      begin
         A;
      end Nested;
   begin
      Nested;
   end C;
      
begin
   A;
   A;
   C;
   Put_Line ("bye");
   Put_Line ("bye");
   Put_Line ("bye");
end proc;
