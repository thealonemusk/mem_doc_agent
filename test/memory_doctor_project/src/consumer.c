#include "data_types.h"
#include "allocators.h"
#include "FreeRTOS.h"
#include "task.h"

void vConsumerTask(void *pvParameters) {
    (void)pvParameters;
    PaymentPayload_t* received_payment;
    
    for(;;) {
        if (xQueueReceive(paymentQueue, &received_payment, portMAX_DELAY) == pdPASS) {
            if (received_payment->amount < 0.0f) {
                continue;
            }
            
            paytm_free(received_payment);
        }
    }
}
