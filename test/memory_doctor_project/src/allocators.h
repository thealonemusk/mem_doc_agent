#ifndef ALLOCATORS_H
#define ALLOCATORS_H

#include <stdlib.h>

void* SB_malloc(size_t size);
void* paytm_malloc(size_t size);
void SB_free(void* ptr);
void paytm_free(void* ptr);

#endif
