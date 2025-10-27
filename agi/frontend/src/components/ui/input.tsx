import * as React from "react";

import { cn } from "../../lib/utils";

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "bg-white text-black border-zinc-300 placeholder:text-zinc-400 flex h-9 w-full min-w-0 rounded-md border px-3 py-1 text-sm transition-[color,box-shadow] outline-none file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50",
        "focus-visible:border-black focus-visible:ring-black/20 focus-visible:ring-2",
        className,
      )}
      {...props}
    />
  );
}

export { Input };
