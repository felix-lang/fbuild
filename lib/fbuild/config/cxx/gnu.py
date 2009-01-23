import fbuild.config.cxx as cxx

# ------------------------------------------------------------------------------

class hash_map(cxx.Header):
    header = 'hash_map'

    hash_map = cxx.template_test(test_types=['int', 'int'])

class ext_hash_map(cxx.Header):
    header = 'ext/hash_map'
    namespace = 'ext'

    hash_map = cxx.template_test(test_types=['int', 'int'])

class gcc_cxx_hash_map(cxx.Header):
    header = 'ext/hash_map'
    namespace = '__gnu_cxx'

    hash_map = cxx.template_test(test_types=['int', 'int'])

# ------------------------------------------------------------------------------

class hash_set(cxx.Header):
    header = 'hash_set'

    hash_set = cxx.template_test(test_types=['int', 'int'])

class ext_hash_set(cxx.Header):
    header = 'ext/hash_set'
    namespace = 'ext'

    hash_set = cxx.template_test(test_types=['int', 'int'])

class gcc_cxx_hash_set(cxx.Header):
    header = 'ext/hash_set'
    namespace = '__gnu_cxx'

    hash_set = cxx.template_test(test_types=['int', 'int'])
