#include <stdio.h>

#ifdef __cplusplus
extern "C"
#endif
extern char* bar();

int main(int argc, char** argv) {
	printf("hello %s\n", bar());
	return 0;
}
