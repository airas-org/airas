"use client";

/*
 * Documentation:
 * Switch — https://app.subframe.com/32f8a386b602/library?component=Switch_7a464794-9ea9-4040-b1de-5bfb2ce599d9
 */

import * as SubframeCore from "@subframe/core";
import React from "react";
import * as SubframeUtils from "../utils";

interface ThumbProps extends React.ComponentProps<typeof SubframeCore.Switch.Thumb> {
  className?: string;
}

const Thumb = React.forwardRef<HTMLDivElement, ThumbProps>(function Thumb(
  { className, ...otherProps }: ThumbProps,
  ref,
) {
  return (
    <SubframeCore.Switch.Thumb asChild={true} {...otherProps}>
      <div
        className={SubframeUtils.twClassNames(
          "flex h-3.5 w-3.5 flex-col items-start gap-2 rounded-full bg-white shadow-sm",
          className,
        )}
        ref={ref}
      />
    </SubframeCore.Switch.Thumb>
  );
});

interface SwitchRootProps extends React.ComponentProps<typeof SubframeCore.Switch.Root> {
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
  className?: string;
}

const SwitchRoot = React.forwardRef<HTMLDivElement, SwitchRootProps>(function SwitchRoot(
  { checked = false, className, ...otherProps }: SwitchRootProps,
  ref,
) {
  return (
    <SubframeCore.Switch.Root checked={checked} asChild={true} {...otherProps}>
      <div
        className={SubframeUtils.twClassNames(
          "group/7a464794 flex h-5 w-8 cursor-pointer flex-col items-start justify-center gap-2 rounded-full border border-solid border-neutral-200 bg-neutral-200 px-0.5 py-0.5 aria-[checked=true]:border aria-[checked=true]:border-solid aria-[checked=true]:border-brand-600 aria-[checked=true]:bg-brand-600",
          className,
        )}
        ref={ref}
      >
        <Thumb />
      </div>
    </SubframeCore.Switch.Root>
  );
});

export const Switch = Object.assign(SwitchRoot, {
  Thumb,
});
