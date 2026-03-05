"use client";

/*
 * Documentation:
 * Icon Button — https://app.subframe.com/32f8a386b602/library?component=Icon+Button_af9405b1-8c54-4e01-9786-5aad308224f6
 */

import * as SubframeCore from "@subframe/core";
import { FeatherPlus } from "@subframe/core";
import React from "react";
import * as SubframeUtils from "../utils";

interface IconButtonRootProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  disabled?: boolean;
  variant?:
    | "brand-primary"
    | "brand-secondary"
    | "brand-tertiary"
    | "neutral-primary"
    | "neutral-secondary"
    | "neutral-tertiary"
    | "destructive-primary"
    | "destructive-secondary"
    | "destructive-tertiary"
    | "inverse";
  size?: "large" | "medium" | "small";
  icon?: React.ReactNode;
  loading?: boolean;
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  className?: string;
}

const IconButtonRoot = React.forwardRef<HTMLButtonElement, IconButtonRootProps>(
  function IconButtonRoot(
    {
      disabled = false,
      variant = "neutral-tertiary",
      size = "medium",
      icon = <FeatherPlus />,
      loading = false,
      className,
      type = "button",
      ...otherProps
    }: IconButtonRootProps,
    ref,
  ) {
    return (
      <button
        className={SubframeUtils.twClassNames(
          "group/af9405b1 flex h-8 w-8 cursor-pointer items-center justify-center gap-2 rounded-md border-none bg-transparent text-left hover:bg-neutral-100 active:bg-neutral-50 disabled:cursor-default disabled:bg-neutral-100 active:disabled:cursor-default active:disabled:bg-neutral-100",
          {
            "h-6 w-6": size === "small",
            "h-10 w-10": size === "large",
            "hover:bg-[#ffffff29] active:bg-[#ffffff3d]": variant === "inverse",
            "hover:bg-error-50 active:bg-error-100": variant === "destructive-tertiary",
            "bg-error-50 hover:bg-error-100 active:bg-error-50":
              variant === "destructive-secondary",
            "bg-error-600 hover:bg-error-500 active:bg-error-600":
              variant === "destructive-primary",
            "border border-solid border-neutral-border bg-white active:bg-white":
              variant === "neutral-secondary",
            "bg-neutral-100 hover:bg-neutral-200 active:bg-neutral-100":
              variant === "neutral-primary",
            "hover:bg-brand-50 active:bg-brand-100": variant === "brand-tertiary",
            "bg-brand-50 hover:bg-brand-100 active:bg-brand-50": variant === "brand-secondary",
            "bg-brand-600 hover:bg-brand-500 active:bg-brand-600": variant === "brand-primary",
          },
          className,
        )}
        ref={ref}
        type={type}
        disabled={disabled}
        {...otherProps}
      >
        {icon ? (
          <SubframeCore.IconWrapper
            className={SubframeUtils.twClassNames(
              "text-heading-3 font-heading-3 text-neutral-700 group-disabled/af9405b1:text-neutral-400",
              {
                hidden: loading,
                "text-body font-body": size === "small",
                "text-white":
                  variant === "inverse" ||
                  variant === "destructive-primary" ||
                  variant === "brand-primary",
                "text-error-700":
                  variant === "destructive-tertiary" || variant === "destructive-secondary",
                "text-brand-700": variant === "brand-tertiary" || variant === "brand-secondary",
              },
            )}
          >
            {icon}
          </SubframeCore.IconWrapper>
        ) : null}
        <SubframeCore.Loader
          className={SubframeUtils.twClassNames(
            "hidden text-caption font-caption text-neutral-700 group-disabled/af9405b1:text-neutral-400",
            {
              "inline-block": loading,
              "text-white":
                variant === "inverse" ||
                variant === "destructive-primary" ||
                variant === "brand-primary",
              "text-error-700":
                variant === "destructive-tertiary" || variant === "destructive-secondary",
              "text-brand-700": variant === "brand-tertiary" || variant === "brand-secondary",
            },
          )}
        />
      </button>
    );
  },
);

export const IconButton = IconButtonRoot;
