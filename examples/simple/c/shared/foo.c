#include <stdio.h>

char* bar();

int main(int argc, char** argv) {
	printf("hello %s\n", bar());
	return 0;
}
