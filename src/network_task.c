#include "network_task.h"
#include "data_types.h"
#include "FreeRTOS.h"
#include "task.h"

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