#include "data_types.h"
#include "factory.h"
#include "allocators.h"
#include "FreeRTOS.h"
#include "task.h"

void vProducerTask(void *pvParameters) {
    (void)pvParameters;
    for(;;) {
        PaymentPayload_t* new_payment = create_payment_payload(80085, 250.0f);
        
        if (new_payment != NULL) {
            if (xQueueSend(paymentQueue, &new_payment, portMAX_DELAY) != pdPASS) {
                return;
            }
        }
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}
