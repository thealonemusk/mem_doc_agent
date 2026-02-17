#ifndef DATA_TYPES_H
#define DATA_TYPES_H

#include "FreeRTOS.h"
#include "queue.h"

typedef struct {
    int transaction_id;
    float amount;
} PaymentPayload_t;

extern QueueHandle_t paymentQueue;

#endif
