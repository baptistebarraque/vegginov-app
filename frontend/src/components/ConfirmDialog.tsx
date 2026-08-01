import * as Dialog from "@radix-ui/react-dialog";
import { type ReactNode } from "react";
import { Button } from "./ui/Button";

interface ConfirmDialogProps {
  /** Optional element that opens the dialog; omit when driving `open` directly. */
  trigger?: ReactNode;
  title: string;
  description?: string;
  confirmLabel: string;
  cancelLabel?: string;
  onConfirm: () => void;
  loading?: boolean;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

// Radix dialog handles the focus trap, Escape, and dialog semantics; styling is
// mapped to the tokens (docs/FRONTEND.md §4). Used for destructive admin
// confirmations (delete a recipe).
function ConfirmDialog({
  trigger,
  title,
  description,
  confirmLabel,
  cancelLabel = "Annuler",
  onConfirm,
  loading = false,
  open,
  onOpenChange,
}: ConfirmDialogProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      {trigger && <Dialog.Trigger asChild>{trigger}</Dialog.Trigger>}
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-nuit/80" />
        <Dialog.Content className="fixed top-1/2 left-1/2 z-50 w-[calc(100%-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border border-lisiere bg-feuille p-6 shadow-[0_1px_2px_rgb(0_0_0/0.4)] focus:outline-none">
          <Dialog.Title className="font-display text-xl text-craie">{title}</Dialog.Title>
          {description && (
            <Dialog.Description className="mt-2 text-sm text-sauge">
              {description}
            </Dialog.Description>
          )}
          <div className="mt-6 flex justify-end gap-2">
            <Dialog.Close asChild>
              <Button variant="ghost" type="button">
                {cancelLabel}
              </Button>
            </Dialog.Close>
            <Button variant="destructive" type="button" loading={loading} onClick={onConfirm}>
              {confirmLabel}
            </Button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

export { ConfirmDialog };
