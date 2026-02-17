#include "producer.h"
#include "data_types.h"
#include "FreeRTOS.h"
#include "task.h"

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