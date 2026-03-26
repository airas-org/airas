/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelSubscriptionResponse } from '../models/CancelSubscriptionResponse';
import type { CheckoutRequest } from '../models/CheckoutRequest';
import type { CheckoutResponse } from '../models/CheckoutResponse';
import type { WebhookReceivedResponse } from '../models/WebhookReceivedResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class EeStripeService {
    /**
     * Create Checkout
     * @param requestBody
     * @returns CheckoutResponse Successful Response
     * @throws ApiError
     */
    public static createCheckoutAirasEeStripeCheckoutPost(
        requestBody: CheckoutRequest,
    ): CancelablePromise<CheckoutResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/ee/stripe/checkout',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Cancel Subscription
     * @returns CancelSubscriptionResponse Successful Response
     * @throws ApiError
     */
    public static cancelSubscriptionAirasEeStripeCancelPost(): CancelablePromise<CancelSubscriptionResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/ee/stripe/cancel',
        });
    }
    /**
     * Stripe Webhook
     * @returns WebhookReceivedResponse Successful Response
     * @throws ApiError
     */
    public static stripeWebhookAirasEeStripeWebhookPost(): CancelablePromise<WebhookReceivedResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/ee/stripe/webhook',
        });
    }
}
