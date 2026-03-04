"use client";

/*
 * Documentation:
 * Progress — https://app.subframe.com/32f8a386b602/library?component=Progress_60964db0-a1bf-428b-b9d5-f34cdf58ea77
 */

import * as SubframeCore from "@subframe/core";
import React from "react";
import * as SubframeUtils from "../utils";

interface IndicatorProps extends React.ComponentProps<typeof SubframeCore.Progress.Indicator> {
  className?: string;
}

const Indicator = React.forwardRef<HTMLDivElement, IndicatorProps>(function Indicator(
  { className, ...otherProps }: IndicatorProps,
  ref,
) {
  return (
    <SubframeCore.Progress.Indicator asChild={true} {...otherProps}>
      <div
        className={SubframeUtils.twClassNames(
          "flex h-2 w-full flex-col items-start gap-2 rounded-full bg-brand-600",
          className,
        )}
        ref={ref}
      />
    </SubframeCore.Progress.Indicator>
  );
});

interface ProgressRootProps extends React.ComponentProps<typeof SubframeCore.Progress.Root> {
  value?: number;
  className?: string;
}

const ProgressRoot = React.forwardRef<HTMLDivElement, ProgressRootProps>(function ProgressRoot(
  { value = 30, className, ...otherProps }: ProgressRootProps,
  ref,
) {
  return (
    <SubframeCore.Progress.Root asChild={true} value={value} {...otherProps}>
      <div
        className={SubframeUtils.twClassNames(
          "flex w-full flex-col items-start gap-2 overflow-hidden rounded-full bg-neutral-100",
          className,
        )}
        ref={ref}
      >
        <Indicator />
      </div>
    </SubframeCore.Progress.Root>
  );
});

export const Progress = Object.assign(ProgressRoot, {
  Indicator,
});
