import { useState } from "react";
import { Upload, FileText, File, Mail, Loader2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useStartup } from "@/contexts/StartupContext";

interface UploadZoneProps {
  onUpload: () => void;
}

const UploadZone = ({ onUpload }: UploadZoneProps) => {
  const [isDragActive, setIsDragActive] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    startupName: '',
    deckText: '',
    transcriptText: '',
    publicUrls: '',
  });
  
  const { analyzeStartup, isLoading, error } = useStartup();

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
    setShowForm(true);
  };

  const handleFileSelect = () => {
    setShowForm(true);
  };

  const handleAnalyze = async () => {
    if (!formData.startupName.trim()) {
      alert('Please enter a startup name');
      return;
    }

    const publicUrls = formData.publicUrls
      .split('\n')
      .map(url => url.trim())
      .filter(url => url.length > 0);

    try {
      await analyzeStartup({
        startupName: formData.startupName,
        deckText: formData.deckText || undefined,
        transcriptText: formData.transcriptText || undefined,
        publicUrls: publicUrls.length > 0 ? publicUrls : undefined,
      });
      onUpload();
    } catch (err) {
      console.error('Analysis failed:', err);
    }
  };

  if (showForm) {
    return (
      <Card className="w-full max-w-2xl">
        <div className="p-6">
          <h3 className="text-xl font-semibold text-foreground mb-6">
            Analyze Startup
          </h3>
          
          <div className="space-y-4">
            <div>
              <Label htmlFor="startupName">Startup Name *</Label>
              <Input
                id="startupName"
                value={formData.startupName}
                onChange={(e) => setFormData(prev => ({ ...prev, startupName: e.target.value }))}
                placeholder="Enter startup name"
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="deckText">Pitch Deck Content</Label>
              <Textarea
                id="deckText"
                value={formData.deckText}
                onChange={(e) => setFormData(prev => ({ ...prev, deckText: e.target.value }))}
                placeholder="Paste pitch deck content here..."
                className="mt-1 min-h-[100px]"
              />
            </div>

            <div>
              <Label htmlFor="transcriptText">Interview/Transcript</Label>
              <Textarea
                id="transcriptText"
                value={formData.transcriptText}
                onChange={(e) => setFormData(prev => ({ ...prev, transcriptText: e.target.value }))}
                placeholder="Paste founder interview or transcript here..."
                className="mt-1 min-h-[100px]"
              />
            </div>

            <div>
              <Label htmlFor="publicUrls">Public URLs (one per line)</Label>
              <Textarea
                id="publicUrls"
                value={formData.publicUrls}
                onChange={(e) => setFormData(prev => ({ ...prev, publicUrls: e.target.value }))}
                placeholder="https://example.com/news&#10;https://crunchbase.com/company/startup"
                className="mt-1 min-h-[80px]"
              />
            </div>

            {error && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}

            <div className="flex space-x-3 pt-4">
              <Button
                onClick={handleAnalyze}
                disabled={isLoading || !formData.startupName.trim()}
                className="flex-1"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  'Analyze Startup'
                )}
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowForm(false)}
                disabled={isLoading}
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      </Card>
    );
  }

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