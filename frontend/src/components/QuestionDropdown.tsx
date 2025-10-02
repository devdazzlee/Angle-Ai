import React, { useState } from 'react';

interface QuestionDropdownProps {
  options: string[];
  onSubmit: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

const QuestionDropdown: React.FC<QuestionDropdownProps> = ({
  options,
  onSubmit,
  placeholder = "Select an option...",
  disabled = false
}) => {
  const [selectedValue, setSelectedValue] = useState<string>('');
  const [isOpen, setIsOpen] = useState(false);

  const handleOptionSelect = (value: string) => {
    setSelectedValue(value);
    setIsOpen(false);
    onSubmit(value);
  };

  const getOptionIcon = (option: string) => {
    const optionLower = option.toLowerCase();
    if (optionLower.includes('yes')) return '✅';
    if (optionLower.includes('no')) return '❌';
    if (optionLower.includes('full-time')) return '💼';
    if (optionLower.includes('part-time')) return '⏰';
    if (optionLower.includes('student')) return '🎓';
    if (optionLower.includes('unemployed')) return '🔍';
    if (optionLower.includes('freelancer') || optionLower.includes('self-employed')) return '🚀';
    if (optionLower.includes('other')) return '📝';
    return '🔹';
  };

  const isYesNoQuestion = options.length === 2 && 
    options.some(opt => opt.toLowerCase().includes('yes')) && 
    options.some(opt => opt.toLowerCase().includes('no'));

  return (
    <div className="bg-gradient-to-br from-slate-50 to-teal-50 rounded-xl p-6 shadow-lg border border-white/50">
      {/* Header */}
      <div className="text-center mb-4">
        <h3 className="text-lg font-bold text-gray-900 mb-2">
          {isYesNoQuestion ? 'Choose Your Answer' : 'Choose Your Answer'}
        </h3>
        <p className="text-gray-600 text-sm">
          {isYesNoQuestion 
            ? 'Select Yes or No to continue' 
            : 'Select the option that best describes your situation'
          }
        </p>
      </div>

      {/* Options Grid */}
      <div className={`grid gap-3 mb-6 ${isYesNoQuestion ? 'grid-cols-2' : 'grid-cols-1'}`}>
        {options.map((option, index) => (
          <button
            key={index}
            onClick={() => handleOptionSelect(option)}
            disabled={disabled}
            className={`
              group relative p-4 rounded-xl border-2 transition-all duration-200 text-left
              ${selectedValue === option
                ? 'border-teal-500 bg-gradient-to-r from-teal-50 to-blue-50 shadow-md transform scale-[1.02]'
                : 'border-gray-200 bg-white hover:border-teal-300 hover:shadow-md hover:transform hover:scale-[1.01]'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              ${isYesNoQuestion ? 'text-center' : ''}
            `}
          >
            <div className={`flex items-center gap-3 ${isYesNoQuestion ? 'flex-col' : ''}`}>
              {/* Icon */}
              <div className={`
                ${isYesNoQuestion ? 'w-16 h-16' : 'w-10 h-10'} rounded-full flex items-center justify-center text-lg transition-all duration-200
                ${selectedValue === option
                  ? 'bg-gradient-to-r from-teal-500 to-blue-500 text-white shadow-lg'
                  : 'bg-gray-100 group-hover:bg-teal-100'
                }
              `}>
                {getOptionIcon(option)}
              </div>
              
              {/* Text */}
              <div className="flex-1">
                <span className={`
                  font-medium transition-colors duration-200 text-lg
                  ${selectedValue === option ? 'text-teal-700' : 'text-gray-700 group-hover:text-teal-700'}
                `}>
                  {option}
                </span>
              </div>

              {/* Selection Indicator */}
              {selectedValue === option && (
                <div className="w-6 h-6 bg-gradient-to-r from-teal-500 to-blue-500 rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              )}
            </div>

            {/* Hover Effect Overlay */}
            <div className={`
              absolute inset-0 rounded-xl bg-gradient-to-r from-teal-500/5 to-blue-500/5 
              transition-opacity duration-200 pointer-events-none
              ${selectedValue === option ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}
            `} />
          </button>
        ))}
      </div>

      {/* Submit Button */}
      {selectedValue && (
        <div className="flex justify-center">
          <button
            onClick={() => onSubmit(selectedValue)}
            disabled={disabled}
            className="
              px-8 py-3 bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 
              text-white font-medium rounded-xl shadow-lg hover:shadow-xl 
              transition-all duration-200 transform hover:scale-105
              disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none
            "
          >
            <div className="flex items-center gap-2">
              <span>Confirm Selection</span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </button>
        </div>
      )}

      {/* Progress Indicator */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-center gap-2">
          <div className="flex gap-1">
            {options.map((_, index) => (
              <div
                key={index}
                className={`
                  w-2 h-2 rounded-full transition-all duration-200
                  ${selectedValue === options[index] 
                    ? 'bg-gradient-to-r from-teal-500 to-blue-500 scale-125' 
                    : 'bg-gray-300'
                  }
                `}
              />
            ))}
          </div>
          <span className="text-xs text-gray-500 ml-2">
            {selectedValue ? 'Selected' : 'Choose an option'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default QuestionDropdown;



