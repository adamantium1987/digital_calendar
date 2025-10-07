import React from 'react';
import { Calendar, CheckSquare, Inbox, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import styles from './EmptyState.module.css';

interface EmptyStateProps {
  variant: 'calendar' | 'tasks' | 'general' | 'error';
  title?: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  variant,
  title,
  description,
  action,
}) => {
  const getIcon = () => {
    switch (variant) {
      case 'calendar':
        return <Calendar size={64} strokeWidth={1.5} />;
      case 'tasks':
        return <CheckSquare size={64} strokeWidth={1.5} />;
      case 'error':
        return <AlertCircle size={64} strokeWidth={1.5} />;
      default:
        return <Inbox size={64} strokeWidth={1.5} />;
    }
  };

  const getDefaultContent = () => {
    switch (variant) {
      case 'calendar':
        return {
          title: title || 'No Events',
          description:
            description || 'You have no events scheduled for this time period.',
        };
      case 'tasks':
        return {
          title: title || 'No Tasks',
          description: description || 'All caught up! You have no pending tasks.',
        };
      case 'error':
        return {
          title: title || 'Something went wrong',
          description:
            description || 'We encountered an error loading your data. Please try again.',
        };
      default:
        return {
          title: title || 'No Data',
          description: description || 'There is no data to display.',
        };
    }
  };

  const content = getDefaultContent();

  return (
    <motion.div
      className={styles.emptyState}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <motion.div
        className={styles.iconContainer}
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
      >
        {getIcon()}
      </motion.div>
      <h3 className={styles.title}>{content.title}</h3>
      <p className={styles.description}>{content.description}</p>
      {action && (
        <motion.button
          className={styles.actionButton}
          onClick={action.onClick}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {action.label}
        </motion.button>
      )}
    </motion.div>
  );
};

export default EmptyState;
