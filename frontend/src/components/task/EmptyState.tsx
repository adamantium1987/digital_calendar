// src/components/EmptyState.tsx
import React, { FC } from "react";

export const EmptyState: FC<{ title?: string; message?: React.ReactNode }> = ({ title = "No items", message }) => (
  <div className="card">
    <div className="no-events">
      <h3>{title}</h3>
      <p>{message ?? "No data available."}</p>
    </div>
  </div>
);

export default EmptyState;
