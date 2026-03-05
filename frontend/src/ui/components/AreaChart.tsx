"use client";

/*
 * Documentation:
 * Area Chart — https://app.subframe.com/32f8a386b602/library?component=Area+Chart_8aa1e7b3-5db6-4a62-aa49-137ced21a231
 */

import * as SubframeCore from "@subframe/core";
import React from "react";
import * as SubframeUtils from "../utils";

interface AreaChartRootProps extends React.ComponentProps<typeof SubframeCore.AreaChart> {
  stacked?: boolean;
  className?: string;
}

const AreaChartRoot = React.forwardRef<
  React.ElementRef<typeof SubframeCore.AreaChart>,
  AreaChartRootProps
>(function AreaChartRoot({ stacked = false, className, ...otherProps }: AreaChartRootProps, ref) {
  return (
    <SubframeCore.AreaChart
      className={SubframeUtils.twClassNames("h-80 w-full", className)}
      ref={ref}
      stacked={stacked}
      colors={["#3b82f6", "#bfdbfe", "#2563eb", "#93c5fd", "#1d4ed8", "#60a5fa"]}
      {...otherProps}
    />
  );
});

export const AreaChart = AreaChartRoot;
