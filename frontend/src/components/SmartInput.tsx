import React, { useState, useRef, useEffect } from 'react';
import SkillRatingForm from './SkillRatingForm';
import QuestionDropdown from './QuestionDropdown';

interface SmartInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  loading?: boolean;
  currentQuestion?: string;
}

const SmartInput: React.FC<SmartInputProps> = ({
  value,
  onChange,
  onSubmit,
  placeholder = "Type your response...",
  disabled = false,
  loading = false,
  currentQuestion = ""
}) => {
  const [showRatingForm, setShowRatingForm] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [dropdownOptions, setDropdownOptions] = useState<string[]>([]);
  const [dropdownType, setDropdownType] = useState<'yesno' | 'multiple' | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Detect question type and extract options
  useEffect(() => {
    const question = currentQuestion.toLowerCase();
    
    // Check for skill rating question - make it more specific
    const isSkillRatingQuestion = question.includes('how comfortable are you with these business skills');
    
    if (isSkillRatingQuestion) {
      setShowRatingForm(true);
      setShowDropdown(false);
      return;
    }

    // Check for Yes/No questions
    const isYesNoQuestion = question.includes('yes') && question.includes('no') && 
                           (question.includes('have you') || question.includes('do you') || 
                            question.includes('are you') || question.includes('would you'));
    
    if (isYesNoQuestion) {
      setShowDropdown(true);
      setDropdownType('yesno');
      setDropdownOptions(['Yes', 'No']);
      setShowRatingForm(false);
      return;
    }

    // Check for multiple choice questions based on specific patterns
    const multipleChoiceQuestions = {
      'what is your preferred communication style': ['Conversational', 'Structured'],
      'what\'s your current work situation': ['Full-time employed', 'Part-time', 'Student', 'Unemployed', 'Self-employed/freelancer', 'Other'],
      'what kind of business are you trying to build': ['Side hustle', 'Small business', 'Scalable startup', 'Nonprofit/social venture', 'Other'],
      'do you have any initial funding available': ['None', 'Personal savings', 'Friends/family', 'External funding (loan, investor)', 'Other'],
      'are you planning to seek outside funding in the future': ['Yes', 'No', 'Unsure'],
      'would you like angel to:': ['Be more hands-on (do more tasks for you)', 'Be more of a mentor (guide but let you take the lead)', 'Alternate based on the task'],
      'do you want to connect with service providers': ['Yes', 'No', 'Later'],
      'what type of business structure are you considering': ['LLC', 'Sole proprietorship', 'Corporation', 'Partnership', 'Unsure'],
      'how do you plan to generate revenue': ['Direct sales', 'Subscriptions', 'Advertising', 'Licensing', 'Services', 'Other/Multiple'],
      'will your business be primarily:': ['Online only', 'Physical location only', 'Both online and physical', 'Unsure'],
      'would you like me to be proactive in suggesting next steps and improvements throughout our process': ['Yes, please be proactive', 'Only when I ask', 'Let me decide each time']
    };

    // Check if current question matches any multiple choice pattern
    for (const [pattern, options] of Object.entries(multipleChoiceQuestions)) {
      if (question.includes(pattern)) {
        setShowDropdown(true);
        setDropdownType('multiple');
        setDropdownOptions(options);
        setShowRatingForm(false);
        return;
      }
    }

    // Check for other multiple choice patterns with bullet points
    const hasMultipleOptions = question.includes('•') || question.includes('full-time') || question.includes('part-time');
    if (hasMultipleOptions && !isYesNoQuestion) {
      // Extract options from the question text
      const options = extractOptionsFromQuestion(currentQuestion);
      if (options.length > 2) {
        setShowDropdown(true);
        setDropdownType('multiple');
        setDropdownOptions(options);
        setShowRatingForm(false);
        return;
      }
    }

    // Default to text input
    setShowRatingForm(false);
    setShowDropdown(false);
    setDropdownType(null);
  }, [currentQuestion]);

  // Extract options from question text
  const extractOptionsFromQuestion = (question: string): string[] => {
    const lines = question.split('\n');
    const options: string[] = [];
    
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('•') || trimmed.startsWith('-')) {
        const option = trimmed.substring(1).trim();
        if (option && !option.includes('?')) {
          options.push(option);
        }
      }
    }
    
    return options;
  };

  const handleRatingSubmit = (ratings: number[]) => {
    const ratingString = ratings.join(', ');
    onChange(ratingString);
    onSubmit(ratingString);
    setShowRatingForm(false);
  };

  const handleRatingCancel = () => {
    setShowRatingForm(false);
  };

  const handleDropdownSubmit = (selectedValue: string) => {
    onChange(selectedValue);
    onSubmit(selectedValue);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit(value);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const target = e.target;
    onChange(target.value);
    
    // Auto-resize textarea
    target.style.height = "auto";
    target.style.height = Math.min(target.scrollHeight, 120) + "px";
  };

  if (showRatingForm) {
    return (
      <div className="bg-white/90 backdrop-blur-sm rounded-xl shadow-lg border border-white/50 p-3">
        <SkillRatingForm
          onSubmit={handleRatingSubmit}
          onCancel={handleRatingCancel}
        />
      </div>
    );
  }

  if (showDropdown && dropdownOptions.length > 0) {
    return (
      <QuestionDropdown
        options={dropdownOptions}
        onSubmit={handleDropdownSubmit}
        placeholder={`Select ${dropdownType === 'yesno' ? 'Yes or No' : 'an option'}...`}
        disabled={disabled}
      />
    );
  }

  return (
    <div className="bg-white/90 backdrop-blur-sm rounded-xl shadow-lg border border-white/50 p-3">
      <div className="flex items-center gap-2 sm:gap-3">
        <div className="w-6 h-6 sm:w-7 sm:h-7 bg-gray-300 rounded-full flex items-center justify-center text-xs flex-shrink-0">
          👤
        </div>
        <div className="flex-1 min-w-0">
          <textarea
            ref={textareaRef}
            className="w-full rounded-lg p-2 sm:p-2.5 resize-none text-sm bg-gray-50 text-gray-900 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent focus:bg-white transition-all duration-200 placeholder-gray-500"
            rows={1}
            value={value}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            style={{ minHeight: "38px", maxHeight: "120px" }}
          />
        </div>
        <button
          className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white p-2 sm:p-2.5 rounded-lg font-medium text-sm disabled:opacity-50 shadow-md transition-all duration-200 flex-shrink-0"
          onClick={() => onSubmit(value)}
          disabled={loading || !value.trim()}
        >
          {loading ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
          ) : (
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
              />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
};

export default SmartInput;
