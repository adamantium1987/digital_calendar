import React from 'react';
import styles from './SkeletonLoader.module.css';

interface SkeletonLoaderProps {
  variant?: 'text' | 'circular' | 'rectangular' | 'card' | 'event' | 'task';
  width?: string | number;
  height?: string | number;
  count?: number;
  className?: string;
}

export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  variant = 'rectangular',
  width,
  height,
  count = 1,
  className = '',
}) => {
  const getVariantClass = () => {
    switch (variant) {
      case 'text':
        return styles.skeletonText;
      case 'circular':
        return styles.skeletonCircular;
      case 'card':
        return styles.skeletonCard;
      case 'event':
        return styles.skeletonEvent;
      case 'task':
        return styles.skeletonTask;
      default:
        return styles.skeletonRectangular;
    }
  };

  const style: React.CSSProperties = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
  };

  if (variant === 'card') {
    return (
      <>
        {Array.from({ length: count }).map((_, index) => (
          <div key={index} className={`${styles.skeletonCard} ${className}`}>
            <div className={styles.skeletonCardHeader}>
              <div className={styles.skeletonText} style={{ width: '60%', height: '24px' }} />
            </div>
            <div className={styles.skeletonCardBody}>
              <div className={styles.skeletonText} style={{ width: '100%', height: '16px' }} />
              <div className={styles.skeletonText} style={{ width: '80%', height: '16px' }} />
              <div className={styles.skeletonText} style={{ width: '90%', height: '16px' }} />
            </div>
          </div>
        ))}
      </>
    );
  }

  if (variant === 'event') {
    return (
      <>
        {Array.from({ length: count }).map((_, index) => (
          <div key={index} className={`${styles.skeletonEvent} ${className}`}>
            <div className={styles.skeletonText} style={{ width: '70%', height: '18px' }} />
            <div className={styles.skeletonText} style={{ width: '50%', height: '14px' }} />
          </div>
        ))}
      </>
    );
  }

  if (variant === 'task') {
    return (
      <>
        {Array.from({ length: count }).map((_, index) => (
          <div key={index} className={`${styles.skeletonTask} ${className}`}>
            <div className={styles.skeletonCircular} style={{ width: '20px', height: '20px' }} />
            <div className={styles.skeletonText} style={{ width: '80%', height: '16px' }} />
          </div>
        ))}
      </>
    );
  }

  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className={`${styles.skeleton} ${getVariantClass()} ${className}`}
          style={style}
        />
      ))}
    </>
  );
};

export default SkeletonLoader;
