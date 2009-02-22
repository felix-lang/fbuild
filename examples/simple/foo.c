#include <stdio.h>

#ifdef __cplusplus
extern "C"
#endif
extern int bar();

int main(int argc, char** argv) {
	printf("mike sucks %d\n", bar());
	return 0;
}
