open Sexplib.Std;;

print_endline (string_of_sexp (Lib.sexp_of_foo (Lib.B 5)));;
