"use client";
/*
 * Documentation:
 * OAuth Social Button — https://app.subframe.com/32f8a386b602/library?component=OAuth+Social+Button_f1948f75-65f9-4f21-b3e4-a49511440c26
 */

import React from "react";
import * as SubframeUtils from "../utils";

interface OAuthSocialButtonRootProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children?: React.ReactNode;
  logo?: string;
  disabled?: boolean;
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  className?: string;
}

const OAuthSocialButtonRoot = React.forwardRef<
  HTMLButtonElement,
  OAuthSocialButtonRootProps
>(function OAuthSocialButtonRoot(
  {
    children,
    logo,
    disabled = false,
    className,
    type = "button",
    ...otherProps
  }: OAuthSocialButtonRootProps,
  ref
) {
  return (
    <button
      className={SubframeUtils.twClassNames(
        "group/f1948f75 flex h-10 cursor-pointer items-center justify-center gap-2 rounded-md border border-solid border-neutral-border bg-white px-4 text-left hover:bg-neutral-100 active:bg-neutral-50 disabled:cursor-default disabled:opacity-50 disabled:pointer-events-none",
        className
      )}
      ref={ref}
      type={type}
      disabled={disabled}
      {...otherProps}
    >
      {logo ? (
        <img className="h-5 w-5 flex-none object-cover" src={logo} />
      ) : null}
      {children ? (
        <span className="text-body-bold font-body-bold text-neutral-700">
          {children}
        </span>
      ) : null}
    </button>
  );
});

export const OAuthSocialButton = OAuthSocialButtonRoot;
