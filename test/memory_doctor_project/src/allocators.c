#include "allocators.h"

void* SB_malloc(size_t size) {
    return malloc(size);
}

void* paytm_malloc(size_t size) {
    return malloc(size);
}

void SB_free(void* ptr) {
    free(ptr);
}

void paytm_free(void* ptr) {
    free(ptr);
}
