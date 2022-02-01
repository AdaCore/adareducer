with Ada.Text_IO;
procedure Hello is

   package pack is
      type Aspected is private
        with Type_Invariant => Check (Aspected);

      function Check (C : Aspected) return Boolean is (True);

   private
      type Aspected is null record;
   end pack;
   C : pack.Aspected;
begin
   if C'Size > 0 then
      Ada.Text_IO.Put_Line ("hello");
   end if;
end Hello;
