import React, { useRef, useState } from 'react';
import { Loader2, FileUp } from 'lucide-react';
import toast from 'react-hot-toast';

interface UploadZoneProps {
  onUpload: (files: File[]) => Promise<void>;
  isUploading: boolean;
  uploadProgress: number;
  maxFileSizeMb?: number;
}

export const UploadZone: React.FC<UploadZoneProps> = ({
  onUpload,
  isUploading,
  uploadProgress,
  maxFileSizeMb = 20,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = async (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;

    const filesArray = Array.from(fileList);
    const validFiles: File[] = [];

    for (const file of filesArray) {
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        toast.error(`"${file.name}" is not a PDF`);
        continue;
      }
      if (file.size > maxFileSizeMb * 1024 * 1024) {
        toast.error(`"${file.name}" exceeds ${maxFileSizeMb}MB limit`);
        continue;
      }
      validFiles.push(file);
    }

    if (validFiles.length > 0) {
      await onUpload(validFiles);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    handleFiles(e.dataTransfer.files);
  };

  return (
    <div className="w-full">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`border border-dashed rounded-lg p-2.5 text-center cursor-pointer transition-all duration-150 ${
          isDragOver
            ? 'border-brand-500 bg-brand-500/5'
            : 'border-surface-700 hover:border-surface-500 bg-surface-900/60 hover:bg-surface-900'
        } ${isUploading ? 'pointer-events-none opacity-80' : ''}`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => handleFiles(e.target.files)}
          multiple
          accept=".pdf,application/pdf"
          className="hidden"
        />

        <div className="flex items-center justify-center">
          {isUploading ? (
            <div className="w-full py-0.5">
              <div className="flex items-center justify-center gap-2 mb-1.5">
                <Loader2 className="w-3.5 h-3.5 text-brand-400 animate-spin" />
                <span className="text-xs text-gray-200 font-medium">Uploading & Indexing PDF...</span>
                <span className="text-[10px] font-mono text-gray-400">({uploadProgress}%)</span>
              </div>
              <div className="w-full bg-surface-800 h-1 rounded-full overflow-hidden border border-surface-700/50">
                <div
                  className="bg-brand-500 h-full transition-all duration-300 rounded-full"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2.5 text-left py-0.5">
              <div className="w-6 h-6 rounded-md bg-surface-800 border border-surface-700/90 flex items-center justify-center text-gray-400 shrink-0">
                <FileUp className="w-3.5 h-3.5 text-brand-400" />
              </div>
              <div className="min-w-0">
                <p className="text-xs text-gray-200 font-medium leading-snug">
                  Drop PDF or <span className="text-brand-400 underline underline-offset-2">browse</span>
                </p>
                <p className="text-[10px] text-gray-500 font-mono mt-0.5 leading-none">
                  Up to {maxFileSizeMb}MB • Auto-indexed
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
