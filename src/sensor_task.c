#include "sensor_task.h"
#include "data_types.h"
#include "FreeRTOS.h"
#include "task.h"

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