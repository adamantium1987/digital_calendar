import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Lazy load pages for code splitting - simplified syntax
const Dashboard = lazy(() => import('../pages/Dashboard').then(module => ({
    default: module.Dashboard
})));

const AccountSetup = lazy(() => import('../pages/AccountSetup').then(module => ({
    default: module.AccountSetup
})));

const GoogleSetup = lazy(() => import('../pages/GoogleSetup').then(module => ({
    default: module.GoogleSetup
})));

const AppleSetup = lazy(() => import('../pages/AppleSetup').then(module => ({
    default: module.AppleSetup
})));

const CalendarDisplay = lazy(() => import('../pages/CalendarDisplay').then(module => ({
    default: module.CalendarDisplay
})));

const TaskChartDisplay = lazy(() => import('../pages/TaskChartDisplay').then(module => ({
    default: module.TaskChartDisplay
})));

// Loading component
const LoadingFallback: React.FC = () => (
    <div className="loading-container">
        <div className="loading">Loading...</div>
    </div>
);

// Route configuration
export const AppRoutes: React.FC = () => {
    return (
        <Suspense fallback={<LoadingFallback />}>
            <Routes>
                {/* Main routes */}
                <Route path="/" element={<Dashboard />} />
                <Route path="/setup" element={<AccountSetup />} />
                <Route path="/setup/google" element={<GoogleSetup />} />
                <Route path="/setup/apple" element={<AppleSetup />} />
                <Route path="/display" element={<CalendarDisplay />} />
                <Route path="/tasks" element={<TaskChartDisplay />} />

                {/* Catch all - redirect to dashboard */}
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </Suspense>
    );
};