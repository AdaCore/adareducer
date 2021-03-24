with Ada.Text_IO; use Ada.Text_IO;

package body P is

   procedure B is
   begin
      Put_Line ("hello");
   end B;

   package body Q is
      procedure Foo2 is null;
   end Q;
   package body Q2 is
      package body Q3 is
      end Q3;
      procedure Foo2 is null;
   end Q2;


end P;
