with Ada.Text_IO;

package P is

   procedure B;

   package Q is
      procedure Foo is null;
   end Q;
   package Q2 is
      package Q3 is
         procedure Foo is null;
      end Q3;
      procedure Foo is null;
   end Q2;   

end P;
