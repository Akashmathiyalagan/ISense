import React from 'react';
import { 
  FileText, 
  Download, 
  Eye, 
  RefreshCw, 
  Trash2, 
  CheckCircle2, 
  Clock, 
  AlertTriangle 
} from 'lucide-react';
import { DocumentItem } from '../../types/document';
import { DocumentStatus } from './DocumentStatus';

interface DocumentTableProps {
  documents: DocumentItem[];
  onView?: (doc: DocumentItem) => void;
  onDownload?: (doc: DocumentItem) => void;
  onReplace?: (doc: DocumentItem) => void;
  onDelete?: (doc: DocumentItem) => void;
}

export const DocumentTable: React.FC<DocumentTableProps> = ({
  documents,
  onView,
  onDownload,
  onReplace,
  onDelete,
}) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-600">
          <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-700 uppercase tracking-wider">
            <tr>
              <th scope="col" className="px-5 py-3">Document Name</th>
              <th scope="col" className="px-5 py-3">Category</th>
              <th scope="col" className="px-5 py-3">Status</th>
              <th scope="col" className="px-5 py-3">Information Check Note</th>
              <th scope="col" className="px-5 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {documents.map((doc) => (
              <tr key={doc.id} className="hover:bg-slate-50/70 transition-colors">
                <td className="px-5 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="font-semibold text-slate-900 line-clamp-1">{doc.name}</p>
                      <p className="text-xs text-slate-400">
                        {doc.fileName ? `${doc.fileName} (${doc.fileSize})` : 'Awaiting upload'}
                      </p>
                    </div>
                  </div>
                </td>
                <td className="px-5 py-4 text-xs font-medium text-slate-700">
                  <span className="bg-slate-100 px-2.5 py-1 rounded-md text-slate-700 border border-slate-200/60">
                    {doc.category}
                  </span>
                </td>
                <td className="px-5 py-4">
                  <DocumentStatus status={doc.status} />
                </td>
                <td className="px-5 py-4 text-xs text-slate-500 max-w-xs">
                  {doc.verificationNote ? (
                    <span className="line-clamp-2 leading-relaxed text-[11px] bg-slate-50 p-1.5 rounded border border-slate-100 block">
                      {doc.verificationNote}
                    </span>
                  ) : (
                    <span className="text-slate-400 italic">No notes</span>
                  )}
                </td>
                <td className="px-5 py-4 text-right">
                  <div className="flex items-center justify-end gap-1">
                    {doc.status !== 'Missing' && (
                      <>
                        {onView && (
                          <button
                            onClick={() => onView(doc)}
                            title="View Document"
                            className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        )}
                        {onDownload && (
                          <button
                            onClick={() => onDownload(doc)}
                            title="Download Document"
                            className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                          >
                            <Download className="w-4 h-4" />
                          </button>
                        )}
                      </>
                    )}
                    {onReplace && (
                      <button
                        onClick={() => onReplace(doc)}
                        title="Upload / Replace"
                        className="p-1.5 text-slate-500 hover:text-amber-600 hover:bg-amber-50 rounded transition-colors"
                      >
                        <RefreshCw className="w-4 h-4" />
                      </button>
                    )}
                    {onDelete && doc.status !== 'Missing' && (
                      <button
                        onClick={() => onDelete(doc)}
                        title="Delete Document"
                        className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
