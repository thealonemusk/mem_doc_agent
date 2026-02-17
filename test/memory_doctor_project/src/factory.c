#include "factory.h"
#include "allocators.h"

PaymentPayload_t* create_payment_payload(int id, float amt) {
    PaymentPayload_t* payload = (PaymentPayload_t*)paytm_malloc(sizeof(PaymentPayload_t));
    if (payload != NULL) {
        payload->transaction_id = id;
        payload->amount = amt;
    }
    return payload;
}
