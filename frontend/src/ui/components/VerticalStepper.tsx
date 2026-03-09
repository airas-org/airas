"use client";
/*
 * Documentation:
 * Vertical Stepper — https://app.subframe.com/32f8a386b602/library?component=Vertical+Stepper_bdc0291d-b5be-40c5-ae2f-527a868488b2
 */

import React from "react";
import { FeatherCheck } from "@subframe/core";
import * as SubframeUtils from "../utils";

interface StepProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "completed" | "active";
  stepNumber?: React.ReactNode;
  label?: React.ReactNode;
  firstStep?: boolean;
  lastStep?: boolean;
  children?: React.ReactNode;
  className?: string;
}

const Step = React.forwardRef<HTMLDivElement, StepProps>(function Step(
  {
    variant = "default",
    stepNumber,
    label,
    firstStep = false,
    lastStep = false,
    children,
    className,
    ...otherProps
  }: StepProps,
  ref
) {
  return (
    <div
      className={SubframeUtils.twClassNames(
        "group/b094efab flex h-full w-full items-start gap-3",
        className
      )}
      ref={ref}
      {...otherProps}
    >
      <div
        className={SubframeUtils.twClassNames(
          "flex flex-col items-center gap-1 self-stretch",
          { "h-auto w-auto flex-none": lastStep }
        )}
      >
        <div
          className={SubframeUtils.twClassNames(
            "flex h-2 w-0.5 flex-none flex-col items-center gap-2 bg-neutral-border",
            { hidden: firstStep }
          )}
        />
        <div
          className={SubframeUtils.twClassNames(
            "flex h-7 w-7 flex-none items-center justify-center overflow-hidden rounded-full bg-neutral-100",
            { "bg-brand-100": variant === "active" || variant === "completed" }
          )}
        >
          {stepNumber ? (
            <span
              className={SubframeUtils.twClassNames(
                "text-body-bold font-body-bold text-subtext-color text-center",
                {
                  "text-brand-700": variant === "active",
                  hidden: variant === "completed",
                }
              )}
            >
              {stepNumber}
            </span>
          ) : null}
          <FeatherCheck
            className={SubframeUtils.twClassNames(
              "hidden text-heading-3 font-heading-3 text-brand-700",
              { "inline-flex": variant === "completed" }
            )}
          />
        </div>
        <div
          className={SubframeUtils.twClassNames(
            "flex min-h-[8px] w-0.5 grow shrink-0 basis-0 flex-col items-center gap-2 bg-neutral-border",
            { hidden: lastStep }
          )}
        />
      </div>
      <div
        className={SubframeUtils.twClassNames(
          "flex grow shrink-0 basis-0 flex-col items-center gap-1 py-4",
          { "px-0 pt-4 pb-1": lastStep, "px-0 pt-1 pb-4": firstStep }
        )}
      >
        {label ? (
          <span
            className={SubframeUtils.twClassNames(
              "line-clamp-2 w-full text-body font-body text-subtext-color",
              {
                "text-body-bold font-body-bold text-default-font":
                  variant === "active",
                "text-default-font": variant === "completed",
              }
            )}
          >
            {label}
          </span>
        ) : null}
        {children ? (
          <div className="flex w-full flex-col items-start gap-2">
            {children}
          </div>
        ) : null}
      </div>
    </div>
  );
});

interface VerticalStepperRootProps
  extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode;
  className?: string;
}

const VerticalStepperRoot = React.forwardRef<
  HTMLDivElement,
  VerticalStepperRootProps
>(function VerticalStepperRoot(
  { children, className, ...otherProps }: VerticalStepperRootProps,
  ref
) {
  return children ? (
    <div
      className={SubframeUtils.twClassNames(
        "flex flex-col items-start",
        className
      )}
      ref={ref}
      {...otherProps}
    >
      {children}
    </div>
  ) : null;
});

export const VerticalStepper = Object.assign(VerticalStepperRoot, {
  Step,
});
