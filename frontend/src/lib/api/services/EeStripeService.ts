/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CheckoutRequest } from '../models/CheckoutRequest';
import type { CheckoutResponse } from '../models/CheckoutResponse';
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
     * @returns any Successful Response
     * @throws ApiError
     */
    public static cancelSubscriptionAirasEeStripeCancelPost(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/ee/stripe/cancel',
        });
    }
    /**
     * Stripe Webhook
     * @returns any Successful Response
     * @throws ApiError
     */
    public static stripeWebhookAirasEeStripeWebhookPost(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/ee/stripe/webhook',
        });
    }
}
