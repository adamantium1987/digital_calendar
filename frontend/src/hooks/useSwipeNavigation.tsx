// useSwipeNavigation.ts - Custom hook for swipe navigation
import { useEffect, useRef } from 'react';

interface SwipeNavigationConfig {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  minSwipeDistance?: number;
  preventDefaultTouchMove?: boolean;
}

export const useSwipeNavigation = ({
  onSwipeLeft,
  onSwipeRight,
  minSwipeDistance = 75,
  preventDefaultTouchMove = false
}: SwipeNavigationConfig) => {
  const touchStartX = useRef<number>(0);
  const touchStartY = useRef<number>(0);
  const touchEndX = useRef<number>(0);
  const touchEndY = useRef<number>(0);

  useEffect(() => {
    const handleTouchStart = (e: TouchEvent) => {
      touchStartX.current = e.touches[0].clientX;
      touchStartY.current = e.touches[0].clientY;
    };

    const handleTouchMove = (e: TouchEvent) => {
      touchEndX.current = e.touches[0].clientX;
      touchEndY.current = e.touches[0].clientY;

      // Prevent default if needed (useful for full-page swipes)
      if (preventDefaultTouchMove) {
        const deltaX = Math.abs(touchEndX.current - touchStartX.current);
        const deltaY = Math.abs(touchEndY.current - touchStartY.current);

        // Only prevent if horizontal swipe is dominant
        if (deltaX > deltaY && deltaX > 10) {
          e.preventDefault();
        }
      }
    };

    const handleTouchEnd = () => {
      const deltaX = touchStartX.current - touchEndX.current;
      const deltaY = Math.abs(touchStartY.current - touchEndY.current);

      // Check if horizontal swipe is dominant (not vertical scroll)
      if (Math.abs(deltaX) > deltaY && Math.abs(deltaX) > minSwipeDistance) {
        if (deltaX > 0) {
          // Swiped left
          onSwipeLeft?.();
        } else {
          // Swiped right
          onSwipeRight?.();
        }
      }

      // Reset values
      touchStartX.current = 0;
      touchStartY.current = 0;
      touchEndX.current = 0;
      touchEndY.current = 0;
    };

    document.addEventListener('touchstart', handleTouchStart);
    document.addEventListener('touchmove', handleTouchMove, { passive: !preventDefaultTouchMove });
    document.addEventListener('touchend', handleTouchEnd);

    return () => {
      document.removeEventListener('touchstart', handleTouchStart);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
    };
  }, [onSwipeLeft, onSwipeRight, minSwipeDistance, preventDefaultTouchMove]);
};