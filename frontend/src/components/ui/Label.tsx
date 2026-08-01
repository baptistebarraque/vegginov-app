// Wraps Radix Label for correct htmlFor/id association out of the box.
import * as LabelPrimitive from "@radix-ui/react-label";
import { forwardRef, type ComponentPropsWithoutRef } from "react";
import { cn } from "../../utils/cn";

const Label = forwardRef<HTMLLabelElement, ComponentPropsWithoutRef<typeof LabelPrimitive.Root>>(
  ({ className, ...props }, ref) => (
    <LabelPrimitive.Root
      ref={ref}
      className={cn("text-sm font-medium text-craie", className)}
      {...props}
    />
  ),
);
Label.displayName = "Label";

export { Label };
