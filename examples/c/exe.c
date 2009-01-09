#include <stdio.h>
#include "lib.h"

int main(int argc, char** argv) {
  int x = fred();
  printf("%d\n", x);
	return x != 5;
}
