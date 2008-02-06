#include <stdio.h>

extern int bar();

int main(int argc, char** argv) {
	printf("mike sucks %d\n", bar());
	return 0;
}
