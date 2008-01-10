@system_cache
def epoll(system, compiler):
    try:
        compiler.compile_str("""
            #include <sys/epoll.h>

            int main(int argc, char** argv) {
                int efd = epoll_create(20);
                return (-1 == efd) ? 1 : 0;
            }
            """
        )
    except ExcecutionError:
        return False
    else:
        return True
