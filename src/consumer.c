#include "consumer.h"
#include "data_types.h"
#include "FreeRTOS.h"
#include "task.h"

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