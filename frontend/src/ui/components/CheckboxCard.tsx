"use client";

/*
 * Documentation:
 * Checkbox Card — https://app.subframe.com/32f8a386b602/library?component=Checkbox+Card_de0b4dfb-3946-4702-be52-5678dd71925a
 */

import * as SubframeCore from "@subframe/core";
import { FeatherCheck } from "@subframe/core";
import React from "react";
import * as SubframeUtils from "../utils";

interface CheckboxCardRootProps extends React.ComponentProps<typeof SubframeCore.Checkbox.Root> {
  disabled?: boolean;
  checked?: boolean;
  hideCheckbox?: boolean;
  children?: React.ReactNode;
  onCheckedChange?: (checked: boolean) => void;
  className?: string;
}

const CheckboxCardRoot = React.forwardRef<HTMLButtonElement, CheckboxCardRootProps>(
  function CheckboxCardRoot(
    {
      disabled = false,
      checked = false,
      hideCheckbox = false,
      children,
      className,
      ...otherProps
    }: CheckboxCardRootProps,
    ref,
  ) {
    return (
      <SubframeCore.Checkbox.Root
        checked={checked}
        disabled={disabled}
        asChild={true}
        {...otherProps}
      >
        <button
          className={SubframeUtils.twClassNames(
            "group/de0b4dfb flex cursor-pointer items-center gap-4 rounded-md border border-solid border-neutral-border bg-default-background px-4 py-3 text-left hover:bg-neutral-50 aria-[checked=true]:border aria-[checked=true]:border-solid aria-[checked=true]:border-brand-200 aria-[checked=true]:bg-brand-50 hover:aria-[checked=true]:bg-brand-50 disabled:cursor-default disabled:border disabled:border-solid disabled:border-neutral-100 disabled:bg-neutral-100 hover:disabled:cursor-default hover:disabled:bg-neutral-100",
            className,
          )}
          ref={ref}
        >
          <div
            className={SubframeUtils.twClassNames(
              "flex h-4 w-4 flex-none flex-col items-center justify-center gap-2 rounded-[2px] border-2 border-solid border-neutral-300 group-aria-[checked=true]/de0b4dfb:border group-aria-[checked=true]/de0b4dfb:border-solid group-aria-[checked=true]/de0b4dfb:border-brand-600 group-aria-[checked=true]/de0b4dfb:bg-brand-600 group-disabled/de0b4dfb:border-2 group-disabled/de0b4dfb:border-solid group-disabled/de0b4dfb:border-neutral-200 group-disabled/de0b4dfb:bg-neutral-100",
              { hidden: hideCheckbox },
            )}
          >
            <FeatherCheck className="hidden font-['Inter'] text-[16px] font-[400] leading-[16px] text-white group-aria-[checked=true]/de0b4dfb:inline-flex group-disabled/de0b4dfb:text-neutral-400" />
          </div>
          {children ? (
            <div className="flex grow shrink-0 basis-0 items-center gap-4">{children}</div>
          ) : null}
        </button>
      </SubframeCore.Checkbox.Root>
    );
  },
);

export const CheckboxCard = CheckboxCardRoot;
