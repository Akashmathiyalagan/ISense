import React, { useState, useRef, DragEvent } from 'react';
import { UploadCloud, FileText, CheckCircle, AlertCircle, X } from 'lucide-react';
import { Button } from '../common/Button';
import { ProgressBar } from '../common/ProgressBar';

interface DocumentUploadProps {
  applicationId: string;
  onUploadSuccess: (file: File, category: string) => void;
  onCancel?: () => void;
  initialCategory?: string;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({
  applicationId,
  onUploadSuccess,
  onCancel,
  initialCategory = 'Product Specification',
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [category, setCategory] = useState<string>(initialCategory);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const categories = [
    'Product Specification',
    'Test Report',
    'Manufacturer Certificate',
    'Address Proof',
    'Quality Manual',
    'Marking & Artwork',
    'Legal Mandate',
    'Brand Verification',
  ];

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (file: File) => {
    setUploadError(null);
    const validExtensions = ['pdf', 'jpg', 'jpeg', 'png'];
    const fileExt = file.name.split('.').pop()?.toLowerCase();

    if (!fileExt || !validExtensions.includes(fileExt)) {
      setUploadError('Unsupported file type. Please upload a PDF, JPG, or PNG document.');
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      setUploadError('File size exceeds the 15 MB limit. Please compress or optimize the file.');
      return;
    }

    setSelectedFile(file);
  };

  const handleStartUpload = () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadProgress(10);

    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 95) {
          clearInterval(interval);
          setTimeout(() => {
            setIsUploading(false);
            onUploadSuccess(selectedFile, category);
          }, 300);
          return 100;
        }
        return prev + 25;
      });
    }, 200);
  };

  return (
    <div className="space-y-4">
      {/* Category selector */}
      <div>
        <label className="block text-xs font-semibold text-slate-700 mb-1.5">
          Document Classification / Category
        </label>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-full text-sm bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
      </div>

      {/* Drag & Drop Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !selectedFile && fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-6 text-center transition-all ${
          isDragging
            ? 'border-blue-500 bg-blue-50/50'
            : selectedFile
            ? 'border-emerald-300 bg-emerald-50/20'
            : 'border-slate-300 hover:border-blue-400 bg-slate-50/50 hover:bg-slate-50 cursor-pointer'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          onChange={handleFileChange}
          className="hidden"
        />

        {selectedFile ? (
          <div className="flex items-center justify-between gap-3 text-left">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                <FileText className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-slate-900 truncate">{selectedFile.name}</p>
                <p className="text-xs text-slate-500">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • {selectedFile.type || 'Document'}
                </p>
              </div>
            </div>
            {!isUploading && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedFile(null);
                }}
                className="p-1 text-slate-400 hover:text-slate-600 rounded-md hover:bg-slate-200/50"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
              <UploadCloud className="w-6 h-6" />
            </div>
            <p className="text-sm font-semibold text-slate-800">
              Drag &amp; drop your file here, or{' '}
              <span className="text-blue-600 underline">browse files</span>
            </p>
            <p className="text-xs text-slate-400 mt-1">Supported formats: PDF, JPG, PNG (Max 15MB)</p>
          </div>
        )}
      </div>

      {uploadError && (
        <div className="flex items-center gap-2 p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{uploadError}</span>
        </div>
      )}

      {isUploading && (
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs text-slate-600 font-medium">
            <span>Uploading &amp; checking document metadata...</span>
            <span>{uploadProgress}%</span>
          </div>
          <ProgressBar progress={uploadProgress} size="sm" />
        </div>
      )}

      {/* Compliance / Scope Disclaimer */}
      <p className="text-[11px] text-slate-500 bg-slate-100/70 p-2.5 rounded-lg border border-slate-200/80 leading-relaxed">
        <strong>Document Information Check:</strong> Uploaded documents undergo automated structure and consistency checks. ISense does not legally certify or approve documents; official evaluation is performed exclusively by the Bureau of Indian Standards.
      </p>

      {/* Actions */}
      <div className="flex items-center justify-end gap-3 pt-2">
        {onCancel && (
          <Button type="button" variant="outline" size="sm" onClick={onCancel} disabled={isUploading}>
            Cancel
          </Button>
        )}
        <Button
          type="button"
          variant="primary"
          size="sm"
          disabled={!selectedFile || isUploading}
          isLoading={isUploading}
          onClick={handleStartUpload}
        >
          Upload &amp; Analyze
        </Button>
      </div>
    </div>
  );
};
