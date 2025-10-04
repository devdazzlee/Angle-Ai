// Enhanced Accept/Modify Buttons with compact beautiful design
interface AcceptModifyButtonsProps {
  onAccept: () => void;
  onModify: (currentText: string) => void;
  onDraftMore?: () => void;
  disabled?: boolean;
  currentText?: string;
  showDraftMore?: boolean;
}

export default function AcceptModifyButtons({ 
  onAccept, 
  onModify, 
  onDraftMore, 
  disabled = false, 
  currentText = "",
  showDraftMore = false 
}: AcceptModifyButtonsProps) {
  return (
    <div className="mt-4 p-4 bg-gradient-to-r from-green-50 via-blue-50 to-orange-50 rounded-lg border border-gray-200 shadow-sm">
      {/* Compact Header */}
      <div className="text-center mb-3">
        <div className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white rounded-full shadow-sm border border-gray-200">
          <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-xs font-medium text-gray-700">Ready to proceed?</span>
        </div>
      </div>

      {/* Compact Buttons Grid */}
      <div className="flex flex-col sm:flex-row gap-2 justify-center">
        {/* Accept Button */}
        <button
          onClick={onAccept}
          disabled={disabled}
          className="group relative px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-all duration-300 transform hover:scale-105 hover:shadow-lg disabled:hover:scale-100 disabled:hover:shadow-none flex items-center justify-center gap-2 min-w-[120px]"
        >
          <div className="absolute inset-0 bg-white opacity-0 group-hover:opacity-10 rounded-lg transition-opacity duration-300"></div>
          <svg className="w-4 h-4 transition-transform duration-300 group-hover:scale-110" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <span className="relative z-10">Accept</span>
          <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-green-300 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
        </button>

        {/* Modify Button */}
        <button
          onClick={() => onModify(currentText)}
          disabled={disabled}
          className="group relative px-6 py-3 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-all duration-300 transform hover:scale-105 hover:shadow-lg disabled:hover:scale-100 disabled:hover:shadow-none flex items-center justify-center gap-2 min-w-[120px]"
        >
          <div className="absolute inset-0 bg-white opacity-0 group-hover:opacity-10 rounded-lg transition-opacity duration-300"></div>
          <svg className="w-4 h-4 transition-transform duration-300 group-hover:scale-110" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          <span className="relative z-10">Modify</span>
          <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-orange-300 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
        </button>

        {/* Draft More Button */}
        {showDraftMore && onDraftMore && (
          <button
            onClick={onDraftMore}
            disabled={disabled}
            className="group relative px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-all duration-300 transform hover:scale-105 hover:shadow-lg disabled:hover:scale-100 disabled:hover:shadow-none flex items-center justify-center gap-2 min-w-[120px]"
          >
            <div className="absolute inset-0 bg-white opacity-0 group-hover:opacity-10 rounded-lg transition-opacity duration-300"></div>
            <svg className="w-4 h-4 transition-transform duration-300 group-hover:scale-110" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            <span className="relative z-10">Draft More</span>
            <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-blue-300 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          </button>
        )}
      </div>

      {/* Compact Footer Info */}
      <div className="mt-3 text-center">
        <div className="inline-flex items-center gap-1.5 text-xs text-gray-500 bg-white px-2.5 py-1 rounded-full border border-gray-200">
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>Choose your next action</span>
        </div>
      </div>
    </div>
  );
}
