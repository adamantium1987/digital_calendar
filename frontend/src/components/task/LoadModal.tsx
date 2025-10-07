// src/components/LoadModal.tsx
import React, { FC } from "react";

export interface LoadModalProps {
  open: boolean;
  payload: string;
  setPayload: (v: string) => void;
  onLoadJson: () => Promise<void>;
  onLoadCsv: () => Promise<void>;
  onClose: () => void;
  uploading?: boolean;
}

export const LoadModal: FC<LoadModalProps> = ({ open, payload, setPayload, onLoadJson, onLoadCsv, onClose, uploading }) => {
  if (!open) return null;

  return (
    <div style={{ position: 'fixed', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1200, backgroundColor: 'rgba(0,0,0,0.4)' }}>
      <div className="card" style={{ width: 800, maxWidth: '95%', zIndex: 1201 }}>
        <h3 className="mb-4">Load Tasks (JSON or CSV)</h3>
        <p className="mb-4">Load from CSV file (task_chart.csv) or paste JSON data.</p>

        <div className="form-group">
          <textarea value={payload} onChange={e => setPayload(e.target.value)} rows={6} style={{ fontFamily: 'var(--font-mono)' }} />
          <div className="flex gap-2 justify-end">
            <button onClick={() => setPayload('')} className="btn btn-secondary btn-sm">Clear JSON</button>
            <button onClick={async () => await onLoadJson()} className="btn btn-sm">Load JSON</button>
          </div>
        </div>

        <hr style={{ border: 'none', borderTop: '1px solid var(--border-color)', margin: 'var(--space-4) 0' }} />

        <div className="flex items-center gap-3">
          <button onClick={async () => await onLoadCsv()} disabled={uploading} className="btn">{uploading ? 'Loading...' : 'Load from CSV File'}</button>
          <span className="text-sm flex-1">Reads from ~/.pi_calendar/task_chart.csv</span>
          <button onClick={onClose} className="btn btn-secondary">Close</button>
        </div>
      </div>
    </div>
  );
};

export default LoadModal;
