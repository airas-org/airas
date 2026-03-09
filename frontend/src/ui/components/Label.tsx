"use client";
/*
 * Documentation:
 * Label — https://app.subframe.com/32f8a386b602/library?component=Label_0280eecd-fc50-4053-bff6-a83f6c953b2a
 */

import React from "react";
import * as SubframeUtils from "../utils";

interface LabelRootProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: "default" | "small" | "xsmall";
  uppercase?: boolean;
  children?: React.ReactNode;
  className?: string;
}

const LabelRoot = React.forwardRef<HTMLDivElement, LabelRootProps>(
  function LabelRoot(
    {
      size = "default",
      uppercase = false,
      children,
      className,
      ...otherProps
    }: LabelRootProps,
    ref
  ) {
    return (
      <div
        className={SubframeUtils.twClassNames(
          "group/0280eecd flex items-center gap-2 text-body font-body text-subtext-color select-none",
          {
            "text-body font-body text-subtext-color select-none uppercase":
              uppercase,
            "text-subtext-color select-none text-caption font-caption tracking-wide":
              size === "xsmall",
            "text-subtext-color select-none text-caption font-caption":
              size === "small",
          },
          className
        )}
        ref={ref}
        {...otherProps}
      >
        {children ? (
          <div className="flex items-center gap-2">{children}</div>
        ) : null}
      </div>
    );
  }
);

export const Label = LabelRoot;
