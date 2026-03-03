/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type EphemeralCloudRunnerConfig = {
    type?: string;
    /**
     * Cloud provider ('aws' or 'gcp')
     */
    cloud_provider?: EphemeralCloudRunnerConfig.cloud_provider;
    /**
     * Instance type (e.g., 'g4dn.xlarge' for AWS, 'n1-standard-4' for GCP)
     */
    gpu_instance_type?: string;
    /**
     * Max instance lifetime in hours (safety net for orphaned instances)
     */
    max_instance_hours?: string;
};
export namespace EphemeralCloudRunnerConfig {
    /**
     * Cloud provider ('aws' or 'gcp')
     */
    export enum cloud_provider {
        AWS = 'aws',
        GCP = 'gcp',
    }
}

