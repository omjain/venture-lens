import { useState } from "react";
import { Upload, FileText, File, Mail } from "lucide-react";
import { Card } from "@/components/ui/card";

interface UploadZoneProps {
  onUpload: () => void;
}

const UploadZone = ({ onUpload }: UploadZoneProps) => {
  const [isDragActive, setIsDragActive] = useState(false);

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
    // Simulate file upload
    setTimeout(() => onUpload(), 1500);
  };

  const handleFileSelect = () => {
    // Simulate file upload
    setTimeout(() => onUpload(), 1500);
  };

  return (
    <Card className="w-full max-w-2xl">
      <div
        className={`p-12 border-2 border-dashed rounded-lg transition-all duration-300 ${
          isDragActive
            ? "border-upload-border bg-upload-zone"
            : "border-border bg-background hover:border-upload-border hover:bg-upload-zone"
        }`}
        onDragEnter={handleDragEnter}
        onDragOver={(e) => e.preventDefault()}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="flex flex-col items-center text-center space-y-6">
          <div className="p-4 bg-primary-soft rounded-full">
            <Upload className="w-8 h-8 text-primary" />
          </div>
          
          <div>
            <h3 className="text-xl font-semibold text-foreground mb-2">
              Upload Startup Documents
            </h3>
            <p className="text-muted-foreground mb-6">
              Drag and drop files here, or click to select files
            </p>
          </div>

          <div className="flex space-x-6 text-sm text-muted-foreground">
            <div className="flex items-center space-x-2">
              <FileText className="w-4 h-4" />
              <span>Pitch Decks</span>
            </div>
            <div className="flex items-center space-x-2">
              <File className="w-4 h-4" />
              <span>Transcripts</span>
            </div>
            <div className="flex items-center space-x-2">
              <Mail className="w-4 h-4" />
              <span>Emails</span>
            </div>
          </div>

          <button
            onClick={handleFileSelect}
            className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            Select Files
          </button>

          <p className="text-xs text-muted-foreground">
            Supports PDF, PPTX, DOCX, TXT files up to 50MB
          </p>
        </div>
      </div>
    </Card>
  );
};

export default UploadZone;