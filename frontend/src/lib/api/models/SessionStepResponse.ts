/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { SessionStepType } from "./SessionStepType";
export type SessionStepResponse = {
  id: string;
  session_id: string;
  step_type: SessionStepType;
  content: any;
  schema_version: number;
  created_by: string;
  created_at: string;
  is_completed: boolean;
};
