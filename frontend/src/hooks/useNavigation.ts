import { useNavigate } from 'react-router-dom';
import { useCallback } from 'react';

/**
 * Custom hook for navigation
 * Wraps react-router's useNavigate with additional functionality
 */
export const useNavigation = () => {
  const navigate = useNavigate();

  const navigateTo = useCallback((path: string) => {
    navigate(path);
  }, [navigate]);

  const goBack = useCallback(() => {
    navigate(-1);
  }, [navigate]);

  const goForward = useCallback(() => {
    navigate(1);
  }, [navigate]);

  return {
    navigateTo,
    goBack,
    goForward,
  };
};
