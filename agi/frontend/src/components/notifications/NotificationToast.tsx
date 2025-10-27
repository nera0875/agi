import { toast } from 'sonner'
import { Check, AlertCircle, Info, X } from 'lucide-react'

export type NotificationType = 'success' | 'error' | 'info'

interface NotificationToastProps {
  message: string
  type?: NotificationType
  duration?: number
  action?: {
    label: string
    onClick: () => void
  }
}

/**
 * Displays a toast notification with auto-dismiss
 * Uses sonner library for cross-browser compatibility
 *
 * @example
 * showNotification({
 *   message: 'Operation successful',
 *   type: 'success',
 *   duration: 3000
 * })
 */
export function showNotification({
  message,
  type = 'info',
  duration = 3000,
  action,
}: NotificationToastProps) {
  const icons: Record<NotificationType, React.ReactNode> = {
    success: <Check className="w-4 h-4" />,
    error: <AlertCircle className="w-4 h-4" />,
    info: <Info className="w-4 h-4" />,
  }

  const toastOptions = {
    description: message,
    duration,
    action: action ? { label: action.label, onClick: action.onClick } : undefined,
    closeButton: true,
  }

  switch (type) {
    case 'success':
      toast.success(message, toastOptions)
      break
    case 'error':
      toast.error(message, toastOptions)
      break
    case 'info':
    default:
      toast(message, { ...toastOptions, icon: icons.info })
  }
}

/**
 * Convenience functions for specific notification types
 */
export const Notification = {
  success: (message: string, duration?: number, action?: { label: string; onClick: () => void }) =>
    showNotification({ message, type: 'success', duration, action }),

  error: (message: string, duration?: number, action?: { label: string; onClick: () => void }) =>
    showNotification({ message, type: 'error', duration, action }),

  info: (message: string, duration?: number, action?: { label: string; onClick: () => void }) =>
    showNotification({ message, type: 'info', duration, action }),
}
