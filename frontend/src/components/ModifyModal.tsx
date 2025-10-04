import React, { useState, useEffect, useRef } from 'react';

interface ModifyModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentText: string;
  onSave: (modifiedText: string) => void;
  loading?: boolean;
}

const ModifyModal: React.FC<ModifyModalProps> = ({
  isOpen,
  onClose,
  currentText,
  onSave,
  loading = false
}) => {
  const [modifiedText, setModifiedText] = useState('');
  const [originalText, setOriginalText] = useState('');
  const [showDiff, setShowDiff] = useState(false);
  const [wordCount, setWordCount] = useState(0);
  const [charCount, setCharCount] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (isOpen) {
      setModifiedText(currentText);
      setOriginalText(currentText);
      setShowDiff(false);
      // Focus textarea after modal opens
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
          // Select all text for easy editing
          textareaRef.current.select();
        }
      }, 100);
    }
  }, [isOpen, currentText]);

  useEffect(() => {
    setWordCount(modifiedText.trim().split(/\s+/).filter(word => word.length > 0).length);
    setCharCount(modifiedText.length);
  }, [modifiedText]);

  const handleSave = () => {
    if (modifiedText.trim()) {
      onSave(modifiedText.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSave();
    }
    if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    }
  };

  const handleReset = () => {
    setModifiedText(originalText);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  const hasChanges = modifiedText !== originalText;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-2xl max-w-5xl w-full max-h-[95vh] flex flex-col border border-gray-200">
        {/* Enhanced Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-orange-50 to-red-50">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Modify Response</h2>
              <p className="text-sm text-gray-600">Edit and refine your response below</p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={loading}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Enhanced Content */}
        <div className="flex-1 p-6 overflow-hidden">
          <div className="h-full flex flex-col gap-4">
            {/* Stats and Controls */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <div className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 6l3-3 3 3M4 4h16a2 2 0 012 2v12a2 2 0 01-2 2H4a2 2 0 01-2-2V6a2 2 0 012-2z" />
                  </svg>
                  <span>{wordCount} words</span>
                </div>
                <div className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span>{charCount} characters</span>
                </div>
                {hasChanges && (
                  <div className="flex items-center gap-1 text-orange-600">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                    <span>Unsaved changes</span>
                  </div>
                )}
              </div>
              
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowDiff(!showDiff)}
                  className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors"
                >
                  {showDiff ? 'Hide' : 'Show'} Original
                </button>
                <button
                  onClick={handleReset}
                  disabled={!hasChanges || loading}
                  className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Reset
                </button>
              </div>
            </div>

            {/* Original Text (when toggled) */}
            {showDiff && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Original Text:</h4>
                <div className="text-sm text-gray-600 whitespace-pre-wrap max-h-32 overflow-y-auto">
                  {originalText}
                </div>
              </div>
            )}

            {/* Main Textarea */}
            <div className="flex-1 flex flex-col">
              <label htmlFor="modify-text" className="block text-sm font-medium text-gray-700 mb-2">
                Your Response:
              </label>
              <textarea
                ref={textareaRef}
                id="modify-text"
                value={modifiedText}
                onChange={(e) => setModifiedText(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={loading}
                className="flex-1 w-full p-4 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-orange-500 focus:border-orange-500 disabled:bg-gray-100 disabled:cursor-not-allowed text-gray-900 placeholder-gray-500 leading-relaxed"
                placeholder="Enter your modifications here..."
                style={{ minHeight: '200px' }}
              />
              
              {/* Enhanced Tips */}
              <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
                <div className="flex items-center gap-4">
                  <span>💡 Ctrl+Enter to save</span>
                  <span>⌨️ Esc to cancel</span>
                  <span>🔄 Click Reset to restore original</span>
                </div>
                <div className="text-right">
                  {hasChanges ? (
                    <span className="text-orange-600 font-medium">• Modified</span>
                  ) : (
                    <span className="text-gray-400">No changes</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
          <div className="text-sm text-gray-600">
            {hasChanges ? (
              <span className="text-orange-600">⚠️ You have unsaved changes</span>
            ) : (
              <span>✅ No changes to save</span>
            )}
          </div>
          
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              disabled={loading}
              className="px-6 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={loading || !modifiedText.trim() || !hasChanges}
              className="px-6 py-2 bg-orange-500 hover:bg-orange-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors duration-200 flex items-center gap-2 shadow-sm"
            >
              {loading ? (
                <>
                  <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Saving...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
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

export default ModifyModal;