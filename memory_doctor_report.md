# Memory Doctor - Cursor Remediation Task

### Instructions for AI Agent:
I have extracted the following C functions because they contain memory allocations or RTOS queue handoffs. Please perform a strict Data Flow Analysis to find memory leaks, dangling pointers, double frees, or alias leaks. If you find a violation, directly apply the fix to my codebase.

---

## Target File: `src\consumer.c`
```c
void vConsumerTask(void *pvParameters) {
    (void)pvParameters;
    SensorData_t *pReceivedData;
    for(;;) {
        if(xQueueReceive(dataQueue, &pReceivedData, portMAX_DELAY) == pdPASS) {
            if(pReceivedData->temperature > 100.0f) {
                vPortFree(pReceivedData);
            }
        }
    }
}
```

## Target File: `src\network_task.c`
```c
void vNetworkTask(void *pvParameters) {
    (void)pvParameters;
    SensorPayload_t *pReceivedSensor;
    for(;;) {
        if(xQueueReceive(sensorQueue, &pReceivedSensor, portMAX_DELAY) == pdPASS) {
            NetworkPacket_t *pNetPacket = (NetworkPacket_t *)pvPortMalloc(sizeof(NetworkPacket_t));
            if (pNetPacket == NULL) {
                vPortFree(pReceivedSensor);
                continue;
            }
            pNetPacket->payload = pReceivedSensor;
            if(xQueueSend(networkQueue, &pNetPacket, portMAX_DELAY) != pdPASS) {
                vPortFree(pNetPacket->payload);
                vPortFree(pNetPacket);
            }
        }
    }
}
```

## Target File: `src\producer.c`
```c
void vProducerTask(void *pvParameters) {
    (void)pvParameters;
    for(;;) {
        SensorData_t *pData = (SensorData_t *)pvPortMalloc(sizeof(SensorData_t));
        if(pData != NULL) {
            pData->sensor_id = 1;
            pData->temperature = 25.4f;
            if(xQueueSend(dataQueue, &pData, portMAX_DELAY) != pdPASS) {
                vPortFree(pData);
            }
        }
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}
```

## Target File: `src\sensor_task.c`
```c
void vSensorTask(void *pvParameters) {
    (void)pvParameters;
    for(;;) {
        SensorPayload_t *pSensorData = (SensorPayload_t *)pvPortMalloc(sizeof(SensorPayload_t));
        if(pSensorData != NULL) {
            pSensorData->id = 101;
            pSensorData->value = 42.5f;
            if(xQueueSend(sensorQueue, &pSensorData, portMAX_DELAY) != pdPASS) {
                vPortFree(pSensorData);
            }
        }
        SensorPayload_t *pLostData = (SensorPayload_t *)pvPortMalloc(sizeof(SensorPayload_t));
        if(pLostData != NULL) {
            pLostData->id = 999;
            if (pSensorData != NULL && pSensorData->value > 50.0f) {
                return;
            }
            vPortFree(pLostData);
        }
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}
```

