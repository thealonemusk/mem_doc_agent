#ifndef DATA_TYPES_H
#define DATA_TYPES_H

#include "FreeRTOS.h"
#include "queue.h"

typedef struct {
    int id;
    float value;
} SensorPayload_t;

typedef struct {
    char ip_addr[16];
    SensorPayload_t *payload;
} NetworkPacket_t;

extern QueueHandle_t sensorQueue;
extern QueueHandle_t networkQueue;

#endif