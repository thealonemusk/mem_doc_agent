#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "data_types.h"
#include "sensor_task.h"
#include "network_task.h"

QueueHandle_t sensorQueue;
QueueHandle_t networkQueue;

int main(void) {
    sensorQueue = xQueueCreate(10, sizeof(SensorPayload_t *));
    networkQueue = xQueueCreate(5, sizeof(NetworkPacket_t *));

    if(sensorQueue != NULL && networkQueue != NULL) {
        xTaskCreate(vSensorTask, "Sensor", 1000, NULL, 1, NULL);
        xTaskCreate(vNetworkTask, "Network", 1000, NULL, 1, NULL);
        vTaskStartScheduler();
    }

    for(;;);
    return 0;
}