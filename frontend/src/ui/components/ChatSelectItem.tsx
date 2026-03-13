"use client";
/*
 * Documentation:
 * Chat Select Item — https://app.subframe.com/32f8a386b602/library?component=Chat+Select+Item_4ecc2bc0-3981-4ea5-bac3-8de44cec3d3b
 */

import React from "react";
import { FeatherCheckCircle2 } from "@subframe/core";
import * as SubframeUtils from "../utils";

interface ChatSelectItemRootProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, "title"> {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  selected?: boolean;
  className?: string;
}

const ChatSelectItemRoot = React.forwardRef<
  HTMLDivElement,
  ChatSelectItemRootProps
>(function ChatSelectItemRoot(
  {
    title,
    subtitle,
    selected = false,
    className,
    ...otherProps
  }: ChatSelectItemRootProps,
  ref
) {
  return (
    <div
      className={SubframeUtils.twClassNames(
        "group/4ecc2bc0 flex w-full cursor-pointer items-center gap-4 rounded-md px-3 py-3 hover:bg-neutral-100",
        className
      )}
      ref={ref}
      {...otherProps}
    >
      <div className="flex grow shrink-0 basis-0 flex-col items-start">
        {title ? (
          <span className="text-body font-body text-default-font">{title}</span>
        ) : null}
        {subtitle ? (
          <span className="text-caption font-caption text-subtext-color">
            {subtitle}
          </span>
        ) : null}
      </div>
      <FeatherCheckCircle2
        className={SubframeUtils.twClassNames(
          "hidden text-body font-body text-default-font",
          { "inline-flex text-heading-3 font-heading-3": selected }
        )}
      />
    </div>
  );
});

export const ChatSelectItem = ChatSelectItemRoot;
