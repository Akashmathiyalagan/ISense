import React from 'react';
import { 
  FileText, 
  Download, 
  Eye, 
  RefreshCw, 
  Trash2, 
  ShieldCheck,
  CheckCircle,
  Clock
} from 'lucide-react';
import { DocumentItem } from '../../types/document';
import { DocumentStatus } from './DocumentStatus';

interface DocumentCardProps {
  document: DocumentItem;
  onView?: (doc: DocumentItem) => void;
  onDownload?: (doc: DocumentItem) => void;
  onReplace?: (doc: DocumentItem) => void;
  onDelete?: (doc: DocumentItem) => void;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({
  document,
  onView,
  onDownload,
  onReplace,
  onDelete,
}) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200/90 p-4 shadow-xs hover:border-slate-300 transition-all flex flex-col justify-between">
      <div>
        <div className="flex items-start justify-between gap-2 mb-2">
          <span className="text-[11px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
            {document.category}
          </span>
          <DocumentStatus status={document.status} />
        </div>

        <div className="flex items-start gap-2.5 mt-2">
          <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center shrink-0 mt-0.5">
            <FileText className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <h4 className="text-sm font-semibold text-slate-900 truncate">{document.name}</h4>
            <p className="text-xs text-slate-500 mt-0.5">
              {document.fileName || 'No file uploaded yet'}
              {document.fileSize && ` • ${document.fileSize}`}
            </p>
          </div>
        </div>

        {document.verificationNote && (
          <div className="mt-3 p-2 bg-slate-50 rounded-lg border border-slate-100 text-[11px] text-slate-600 leading-snug">
            <span className="font-semibold text-slate-700">Check Note: </span>
            {document.verificationNote}
          </div>
        )}
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
        <span className="text-[11px] text-slate-400">
          {document.uploadedAt
            ? `Uploaded ${new Date(document.uploadedAt).toLocaleDateString()}`
            : 'Required artifact'}
        </span>

        <div className="flex items-center gap-1">
          {document.status !== 'Missing' && (
            <>
              {onView && (
                <button
                  onClick={() => onView(document)}
                  title="View Document"
                  className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                >
                  <Eye className="w-3.5 h-3.5" />
                </button>
              )}
              {onDownload && (
                <button
                  onClick={() => onDownload(document)}
                  title="Download File"
                  className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                </button>
              )}
            </>
          )}

          {onReplace && (
            <button
              onClick={() => onReplace(document)}
              title="Replace / Re-upload"
              className="p-1.5 text-slate-500 hover:text-amber-600 hover:bg-amber-50 rounded transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          )}

          {onDelete && document.status !== 'Missing' && (
            <button
              onClick={() => onDelete(document)}
              title="Delete Document"
              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
