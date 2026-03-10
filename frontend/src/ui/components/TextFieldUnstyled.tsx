"use client";
/*
 * Documentation:
 * Text Field Unstyled — https://app.subframe.com/32f8a386b602/library?component=Text+Field+Unstyled_abb07b95-d67f-418c-aea5-aba353cce0d4
 */

import React from "react";
import * as SubframeCore from "@subframe/core";
import * as SubframeUtils from "../utils";

interface InputProps
  extends Omit<
    React.InputHTMLAttributes<HTMLInputElement>,
    "type" | "placeholder"
  > {
  type?: "text" | "password" | "email" | "number" | "tel" | "url" | "search";
  placeholder?: React.ReactNode;
  value?: string;
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  className?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(function Input(
  { type = "text", placeholder, className, ...otherProps }: InputProps,
  ref
) {
  return (
    <input
      className={SubframeUtils.twClassNames(
        "group/5ab818fd h-full w-full border-none bg-transparent px-0 py-0 text-body font-body text-default-font outline-none placeholder:text-neutral-400",
        className
      )}
      placeholder={placeholder as string}
      ref={ref}
      type={
        type === "search"
          ? "search"
          : type === "url"
          ? "url"
          : type === "tel"
          ? "tel"
          : type === "number"
          ? "number"
          : type === "email"
          ? "email"
          : type === "password"
          ? "password"
          : "text"
      }
      {...otherProps}
    />
  );
});

interface TextFieldUnstyledRootProps
  extends React.LabelHTMLAttributes<HTMLLabelElement> {
  children?: React.ReactNode;
  className?: string;
}

const TextFieldUnstyledRoot = React.forwardRef<
  HTMLLabelElement,
  TextFieldUnstyledRootProps
>(function TextFieldUnstyledRoot(
  { children, className, ...otherProps }: TextFieldUnstyledRootProps,
  ref
) {
  return children ? (
    <label
      className={SubframeUtils.twClassNames(
        "flex flex-col items-start gap-1",
        className
      )}
      ref={ref}
      {...otherProps}
    >
      {children}
    </label>
  ) : null;
});

export const TextFieldUnstyled = Object.assign(TextFieldUnstyledRoot, {
  Input,
});
