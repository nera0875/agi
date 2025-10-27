import { Toaster } from 'sonner'

/**
 * Toast provider component that should be placed at the root of your app
 * Renders the sonner Toaster instance with default configuration
 *
 * @example
 * In your main layout/app:
 * <ToastProvider />
 */
export function ToastProvider() {
  return (
    <Toaster
      position="top-right"
      richColors
      closeButton
      expand
      visibleToasts={3}
    />
  )
}
