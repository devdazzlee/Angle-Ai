import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';

interface RoadmapEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  roadmapContent: string;
  sessionId: string;
  onSave: (updatedContent: string) => void;
  loading?: boolean;
}

const RoadmapEditModal: React.FC<RoadmapEditModalProps> = ({
  isOpen,
  onClose,
  roadmapContent,
  sessionId,
  onSave,
  loading = false
}) => {
  const [editContent, setEditContent] = useState<string>('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isOpen && roadmapContent) {
      setEditContent(roadmapContent);
    }
  }, [isOpen, roadmapContent]);

  const handleSaveRoadmap = async () => {
    setIsSaving(true);
    try {
      await onSave(editContent);
      toast.success('Roadmap saved successfully!');
    } catch (error) {
      console.error('Error saving roadmap:', error);
      toast.error('Failed to save roadmap');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-[95vw] max-w-6xl h-[90vh] shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between bg-gradient-to-r from-purple-600 to-blue-600 px-6 py-4 text-white">
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center text-2xl">✏️</div>
            <div>
              <h2 className="text-lg font-bold">Edit Roadmap</h2>
              <p className="text-purple-200 text-xs">Customize your roadmap content</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="hover:bg-white/10 p-2 rounded-full transition"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* FORCE SHOW CONTENT - This should always be visible */}
          <div className="bg-red-500 text-white p-4 mb-4 rounded">
            <h3 className="text-lg font-bold">🚨 MODAL CONTENT AREA IS WORKING! 🚨</h3>
            <p>If you can see this red box, the modal content is rendering correctly.</p>
          </div>

          {/* Debug Info */}
          <div className="bg-yellow-100 border-2 border-yellow-500 rounded-lg p-4 mb-6">
            <h4 className="font-bold text-yellow-800 mb-2">DEBUG INFORMATION:</h4>
            <div className="text-sm text-yellow-800 space-y-1">
              <p><strong>Modal Open:</strong> {isOpen ? 'YES' : 'NO'}</p>
              <p><strong>Loading:</strong> {loading ? 'YES' : 'NO'}</p>
              <p><strong>Content Exists:</strong> {roadmapContent ? 'YES' : 'NO'}</p>
              <p><strong>Content Length:</strong> {roadmapContent?.length || 0} characters</p>
            </div>
          </div>

          {/* Simple Text Input */}
          <div className="bg-blue-100 border-2 border-blue-500 rounded-lg p-4 mb-6">
            <h4 className="font-bold text-blue-800 mb-2">EDIT ROADMAP CONTENT:</h4>
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              className="w-full h-96 p-3 border border-gray-300 rounded font-mono text-sm"
              placeholder="Edit your roadmap content here..."
            />
          </div>

          {/* Show current content */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <h4 className="font-semibold text-green-800 mb-2">CURRENT ROADMAP CONTENT:</h4>
            <div className="bg-white p-3 rounded border max-h-64 overflow-y-auto">
              <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                {roadmapContent || 'No roadmap content available'}
              </pre>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-between items-center">
          <div className="text-sm text-gray-600">
            Ready to save your changes
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveRoadmap}
              disabled={isSaving}
              className="bg-purple-500 hover:bg-purple-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              {isSaving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Saving...
                </>
              ) : (
                <>
                  <span>💾</span>
                  Save Changes
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RoadmapEditModal;