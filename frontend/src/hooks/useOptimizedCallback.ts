import { useCallback, useRef } from 'react';

/**
 * Optimized callback hook that persists the function reference
 * but always calls the latest version
 *
 * This is useful when you want to pass a stable reference to child components
 * but the function implementation changes frequently.
 *
 * Example:
 *   const handleClick = useOptimizedCallback((id) => {
 *     // Uses latest state without recreating the function
 *     console.log(currentState, id);
 *   });
 */
export function useOptimizedCallback<T extends (...args: any[]) => any>(
  callback: T
): T {
  const callbackRef = useRef(callback);

  // Update ref on every render
  callbackRef.current = callback;

  // Return stable callback that calls the latest version
  return useCallback(
    ((...args) => callbackRef.current(...args)) as T,
    []
  );
}
