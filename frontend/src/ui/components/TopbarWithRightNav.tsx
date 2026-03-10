"use client";
/*
 * Documentation:
 * Topbar with right nav — https://app.subframe.com/32f8a386b602/library?component=Topbar+with+right+nav_d20e2e52-ba3d-4133-901a-9a15f7f729a9
 */

import React from "react";
import * as SubframeCore from "@subframe/core";
import * as SubframeUtils from "../utils";

interface NavItemProps extends React.HTMLAttributes<HTMLDivElement> {
  selected?: boolean;
  icon?: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
}

const NavItem = React.forwardRef<HTMLDivElement, NavItemProps>(function NavItem(
  {
    selected = false,
    icon = null,
    children,
    className,
    ...otherProps
  }: NavItemProps,
  ref
) {
  return (
    <div
      className={SubframeUtils.twClassNames(
        "group/79ff7d2b flex cursor-pointer items-center justify-center gap-2 rounded-md px-2 py-1",
        className
      )}
      ref={ref}
      {...otherProps}
    >
      {icon ? (
        <SubframeCore.IconWrapper
          className={SubframeUtils.twClassNames(
            "text-heading-3 font-heading-3 text-subtext-color group-hover/79ff7d2b:text-default-font",
            {
              "text-default-font group-hover/79ff7d2b:text-default-font":
                selected,
            }
          )}
        >
          {icon}
        </SubframeCore.IconWrapper>
      ) : null}
      {children ? (
        <span
          className={SubframeUtils.twClassNames(
            "text-body font-body text-subtext-color group-hover/79ff7d2b:text-default-font",
            { "text-body-bold font-body-bold text-default-font": selected }
          )}
        >
          {children}
        </span>
      ) : null}
    </div>
  );
});

interface TopbarWithRightNavRootProps
  extends React.HTMLAttributes<HTMLElement> {
  leftSlot?: React.ReactNode;
  rightSlot?: React.ReactNode;
  className?: string;
}

const TopbarWithRightNavRoot = React.forwardRef<
  HTMLElement,
  TopbarWithRightNavRootProps
>(function TopbarWithRightNavRoot(
  {
    leftSlot,
    rightSlot,
    className,
    ...otherProps
  }: TopbarWithRightNavRootProps,
  ref
) {
  return (
    <nav
      className={SubframeUtils.twClassNames(
        "flex w-full items-center gap-4 bg-default-background px-6 py-4",
        className
      )}
      ref={ref}
      {...otherProps}
    >
      {leftSlot ? (
        <div className="flex items-center gap-4">{leftSlot}</div>
      ) : null}
      {rightSlot ? (
        <div className="flex grow shrink-0 basis-0 items-center justify-end gap-4">
          {rightSlot}
        </div>
      ) : null}
    </nav>
  );
});

export const TopbarWithRightNav = Object.assign(TopbarWithRightNavRoot, {
  NavItem,
});
