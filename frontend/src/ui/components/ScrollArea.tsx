"use client";
/*
 * Documentation:
 * Scroll Area — https://app.subframe.com/32f8a386b602/library?component=Scroll+Area_0da24504-c68a-41cf-afb1-2c8284dcb8f3
 */

import React from "react";
import * as SubframeUtils from "../utils";

interface ScrollAreaRootProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode;
  className?: string;
}

const ScrollAreaRoot = React.forwardRef<HTMLDivElement, ScrollAreaRootProps>(
  function ScrollAreaRoot(
    { children, className, ...otherProps }: ScrollAreaRootProps,
    ref
  ) {
    return (
      <div
        className={SubframeUtils.twClassNames(
          "flex h-full w-full flex-col items-start overflow-auto",
          className
        )}
        ref={ref}
        {...otherProps}
      >
        {children ? (
          <div className="flex w-full flex-col items-start">{children}</div>
        ) : null}
      </div>
    );
  }
);

export const ScrollArea = ScrollAreaRoot;
