import * as React from "react"
import { cn } from "@/lib/utils"

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-md border border-[#e0e0e0] bg-white px-3 py-2 text-[16px] text-[#1a1a1a] transition-colors placeholder:text-gray-500 focus:border-[#1a73e8] focus:outline-none focus:ring-1 focus:ring-[#1a73e8] disabled:cursor-not-allowed disabled:bg-gray-100 disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input } 