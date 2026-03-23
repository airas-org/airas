/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { FeedbackCategory } from './FeedbackCategory';
export type CreateFeedbackRequestBody = {
    category: FeedbackCategory;
    subject: string;
    detail: string;
    email?: (string | null);
};

