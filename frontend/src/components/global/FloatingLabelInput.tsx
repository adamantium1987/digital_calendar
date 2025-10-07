import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import styles from './FloatingLabelInput.module.css';

interface FloatingLabelInputProps {
  id: string;
  label: string;
  type?: 'text' | 'email' | 'password' | 'number' | 'date' | 'time' | 'datetime-local';
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  error?: string;
  icon?: React.ReactNode;
}

export const FloatingLabelInput: React.FC<FloatingLabelInputProps> = ({
  id,
  label,
  type = 'text',
  value,
  onChange,
  placeholder = '',
  required = false,
  disabled = false,
  error,
  icon,
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const isFloating = isFocused || value !== '';

  return (
    <div className={styles.formGroup}>
      <div className={`${styles.inputWrapper} ${error ? styles.error : ''}`}>
        {icon && <div className={styles.icon}>{icon}</div>}
        <input
          ref={inputRef}
          id={id}
          type={type}
          value={value}
          onChange={onChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          required={required}
          disabled={disabled}
          className={`${styles.input} ${icon ? styles.inputWithIcon : ''}`}
        />
        <motion.label
          htmlFor={id}
          className={styles.label}
          initial={false}
          animate={{
            y: isFloating ? -24 : 0,
            scale: isFloating ? 0.85 : 1,
            color: isFocused
              ? 'var(--primary-500)'
              : error
              ? 'var(--error-500)'
              : 'var(--text-secondary)',
          }}
          transition={{ duration: 0.2 }}
        >
          {label}
          {required && <span className={styles.required}>*</span>}
        </motion.label>
        <motion.div
          className={styles.underline}
          initial={false}
          animate={{
            scaleX: isFocused ? 1 : 0,
            backgroundColor: error ? 'var(--error-500)' : 'var(--primary-500)',
          }}
          transition={{ duration: 0.2 }}
        />
      </div>
      {error && (
        <motion.span
          className={styles.errorMessage}
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -5 }}
        >
          {error}
        </motion.span>
      )}
    </div>
  );
};

interface FloatingLabelTextareaProps {
  id: string;
  label: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  error?: string;
  rows?: number;
}

export const FloatingLabelTextarea: React.FC<FloatingLabelTextareaProps> = ({
  id,
  label,
  value,
  onChange,
  placeholder = '',
  required = false,
  disabled = false,
  error,
  rows = 4,
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const isFloating = isFocused || value !== '';

  return (
    <div className={styles.formGroup}>
      <div className={`${styles.inputWrapper} ${error ? styles.error : ''}`}>
        <textarea
          ref={textareaRef}
          id={id}
          value={value}
          onChange={onChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          required={required}
          disabled={disabled}
          rows={rows}
          className={styles.textarea}
        />
        <motion.label
          htmlFor={id}
          className={styles.label}
          initial={false}
          animate={{
            y: isFloating ? -24 : 0,
            scale: isFloating ? 0.85 : 1,
            color: isFocused
              ? 'var(--primary-500)'
              : error
              ? 'var(--error-500)'
              : 'var(--text-secondary)',
          }}
          transition={{ duration: 0.2 }}
        >
          {label}
          {required && <span className={styles.required}>*</span>}
        </motion.label>
        <motion.div
          className={styles.underline}
          initial={false}
          animate={{
            scaleX: isFocused ? 1 : 0,
            backgroundColor: error ? 'var(--error-500)' : 'var(--primary-500)',
          }}
          transition={{ duration: 0.2 }}
        />
      </div>
      {error && (
        <motion.span
          className={styles.errorMessage}
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -5 }}
        >
          {error}
        </motion.span>
      )}
    </div>
  );
};

export default FloatingLabelInput;
