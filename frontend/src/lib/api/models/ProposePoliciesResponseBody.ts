/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ProposedMethodSchema } from './ProposedMethodSchema';
export type ProposePoliciesResponseBody = {
    feasible: boolean;
    infeasible_reason: (string | null);
    proposed_methods: Array<ProposedMethodSchema>;
};

