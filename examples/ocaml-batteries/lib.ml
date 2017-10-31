open Sexplib.Std;;

type foo = A | B of int [@@deriving sexp];;

print_endline (string_of_sexp (sexp_of_foo A));;
