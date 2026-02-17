#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "data_types.h"

QueueHandle_t paymentQueue;
extern void vProducerTask(void *pvParameters);
extern void vConsumerTask(void *pvParameters);

int main(void) {
    paymentQueue = xQueueCreate(10, sizeof(PaymentPayload_t*));
    
    if (paymentQueue != NULL) {
        xTaskCreate(vProducerTask, "Producer", 1000, NULL, 1, NULL);
        xTaskCreate(vConsumerTask, "Consumer", 1000, NULL, 1, NULL);
        vTaskStartScheduler();
    }
    
    for(;;);
    return 0;
}
