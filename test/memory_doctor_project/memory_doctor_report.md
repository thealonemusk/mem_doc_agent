# Memory Doctor - Enterprise Cross-Thread Remediation Task

### Instructions for AI Agent:
I have extracted the following C functions. They contain memory allocations (`SB_malloc`, `paytm_malloc`), custom factory calls, or Inter-Process Communication (IPC) handoffs.

**CRITICAL DIRECTIVES FOR CROSS-THREAD TRACKING:**
1. **Identify the Queue:** Look at the `IPC Producer` functions. Note the name of the queue or mailbox a pointer is sent to.
2. **Bridge the Gap:** Find the corresponding `IPC Consumer` function that reads from that exact same queue name.
3. **Enforce Ownership:** Once the `IPC Consumer` reads the pointer from the queue, it takes ownership. You MUST verify that the Consumer function eventually calls `SB_free` or `paytm_free` on that pointer in all execution paths.
4. If an IPC send fails (e.g., queue is full), ensure the Producer frees the memory before returning.
5. Output the corrected C function for any violations found.

---

## Target File: `src\consumer.c` | Role: Direct Memory Op
```c
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
```

## Target File: `src\factory.c` | Role: Direct Memory Op
```c
PaymentPayload_t* create_payment_payload(int id, float amt) {
    PaymentPayload_t* payload = (PaymentPayload_t*)paytm_malloc(sizeof(PaymentPayload_t));
    if (payload != NULL) {
        payload->transaction_id = id;
        payload->amount = amt;
    }
    return payload;
}
```

## Target File: `src\producer.c` | Role: IPC Producer (Queue Send)
```c
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
```

