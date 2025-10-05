import React, { useState, useEffect } from 'react';
import { 
  Building2, 
  Package, 
  Users, 
  MapPin, 
  DollarSign, 
  Megaphone, 
  Scale, 
  TrendingUp, 
  Shield 
} from 'lucide-react';

interface BusinessPlanSection {
  id: string;
  title: string;
  icon: React.ReactNode;
  startQuestion: number;
  endQuestion: number;
  color: string;
  bgColor: string;
}

interface BusinessPlanProgressWidgetProps {
  currentQuestionNumber: number;
  totalQuestions: number;
  className?: string;
}

const BusinessPlanProgressWidget: React.FC<BusinessPlanProgressWidgetProps> = ({
  currentQuestionNumber,
  totalQuestions,
  className = ""
}) => {
  const [currentSection, setCurrentSection] = useState<BusinessPlanSection | null>(null);
  const [sectionProgress, setSectionProgress] = useState(0);
  const [overallProgress, setOverallProgress] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);

  // Define business plan sections based on constant.py structure
  const sections: BusinessPlanSection[] = [
    {
      id: 'business-foundation',
      title: 'Business Foundation',
      icon: <Building2 className="w-4 h-4" />,
      startQuestion: 1,
      endQuestion: 4,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      id: 'product-service',
      title: 'Product/Service Details',
      icon: <Package className="w-4 h-4" />,
      startQuestion: 5,
      endQuestion: 8,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    },
    {
      id: 'market-research',
      title: 'Market Research',
      icon: <Users className="w-4 h-4" />,
      startQuestion: 9,
      endQuestion: 12,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      id: 'location-operations',
      title: 'Location & Operations',
      icon: <MapPin className="w-4 h-4" />,
      startQuestion: 13,
      endQuestion: 17,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50'
    },
    {
      id: 'financial-planning',
      title: 'Financial Planning',
      icon: <DollarSign className="w-4 h-4" />,
      startQuestion: 18,
      endQuestion: 25,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50'
    },
    {
      id: 'marketing-sales',
      title: 'Marketing & Sales',
      icon: <Megaphone className="w-4 h-4" />,
      startQuestion: 26,
      endQuestion: 31,
      color: 'text-pink-600',
      bgColor: 'bg-pink-50'
    },
    {
      id: 'legal-compliance',
      title: 'Legal & Compliance',
      icon: <Scale className="w-4 h-4" />,
      startQuestion: 32,
      endQuestion: 38,
      color: 'text-red-600',
      bgColor: 'bg-red-50'
    },
    {
      id: 'growth-scaling',
      title: 'Growth & Scaling',
      icon: <TrendingUp className="w-4 h-4" />,
      startQuestion: 39,
      endQuestion: 42,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50'
    },
    {
      id: 'risk-management',
      title: 'Risk Management',
      icon: <Shield className="w-4 h-4" />,
      startQuestion: 43,
      endQuestion: 46,
      color: 'text-gray-600',
      bgColor: 'bg-gray-50'
    }
  ];

  useEffect(() => {
    // Find current section based on question number
    const activeSection = sections.find(
      section => currentQuestionNumber >= section.startQuestion && 
                 currentQuestionNumber <= section.endQuestion
    );

    if (activeSection) {
      setIsAnimating(true);
      
      // Calculate section progress (questions completed within current section)
      const questionsInSection = activeSection.endQuestion - activeSection.startQuestion + 1;
      const questionsCompletedInSection = Math.max(0, currentQuestionNumber - activeSection.startQuestion);
      const progress = (questionsCompletedInSection / questionsInSection) * 100;
      
      setCurrentSection(activeSection);
      setSectionProgress(Math.min(100, Math.max(0, progress)));
      
      // Calculate overall progress
      const overallProgress = Math.min(100, Math.max(0, (currentQuestionNumber / totalQuestions) * 100));
      setOverallProgress(overallProgress);

      // Reset animation after transition
      setTimeout(() => setIsAnimating(false), 300);
    } else {
      // If no section found, try to find the closest section
      const nextSection = sections.find(section => currentQuestionNumber < section.startQuestion);
      if (nextSection) {
        setCurrentSection(nextSection);
        setSectionProgress(0);
        setOverallProgress(Math.min(100, Math.max(0, (currentQuestionNumber / totalQuestions) * 100)));
      }
    }
  }, [currentQuestionNumber, totalQuestions]);

  if (!currentSection) {
    // Fallback for when question number is outside expected range
    return (
      <div className={`bg-white rounded-xl shadow-sm border border-gray-100 p-4 ${className}`}>
        <div className="text-center">
          <h3 className="text-sm font-semibold text-gray-900 mb-2">Business Plan Progress</h3>
          <div className="text-xs text-gray-500">
            Question {currentQuestionNumber} of {totalQuestions}
          </div>
          <div className="mt-2 text-xs text-gray-400">
            Preparing progress tracking...
          </div>
        </div>
      </div>
    );
  }

  const questionsInCurrentSection = currentSection.endQuestion - currentSection.startQuestion + 1;
  const currentQuestionInSection = Math.max(1, currentQuestionNumber - currentSection.startQuestion + 1);

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-100 p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900">Business Plan Progress</h3>
        <div className="text-xs text-gray-500">
          {currentQuestionNumber} of {totalQuestions}
        </div>
      </div>

      {/* Current Section */}
      <div className={`transition-all duration-300 ${isAnimating ? 'scale-105 opacity-80' : 'scale-100 opacity-100'}`}>
        <div className={`flex items-center space-x-3 p-3 rounded-lg ${currentSection.bgColor} border border-gray-100`}>
          <div className={`p-2 rounded-lg ${currentSection.color.replace('text-', 'bg-').replace('-600', '-100')}`}>
            <div className={currentSection.color}>
              {currentSection.icon}
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-gray-900 truncate">
              {currentSection.title}
            </div>
            <div className="text-xs text-gray-600">
              Question {currentQuestionInSection} of {questionsInCurrentSection}
            </div>
          </div>
        </div>
      </div>

      {/* Section Progress Bar */}
      <div className="mt-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs font-medium text-gray-700">Section Progress</span>
          <span className="text-xs text-gray-500">{Math.round(sectionProgress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-500 ease-out ${currentSection.color.replace('text-', 'bg-')}`}
            style={{ width: `${sectionProgress}%` }}
          />
        </div>
      </div>

      {/* Overall Progress */}
      <div className="mt-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs font-medium text-gray-700">Overall Progress</span>
          <span className="text-xs text-gray-500">{Math.round(overallProgress)}%</span>
        </div>
        
        {/* Circular Progress */}
        <div className="relative w-16 h-16 mx-auto">
          <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 64 64">
            {/* Background circle */}
            <circle
              cx="32"
              cy="32"
              r="28"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
              className="text-gray-200"
            />
            {/* Progress circle */}
            <circle
              cx="32"
              cy="32"
              r="28"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
              strokeDasharray={`${2 * Math.PI * 28}`}
              strokeDashoffset={`${2 * Math.PI * 28 * (1 - overallProgress / 100)}`}
              strokeLinecap="round"
              className="text-teal-500 transition-all duration-500 ease-out"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xs font-semibold text-gray-700">
              {Math.round(overallProgress)}%
            </span>
          </div>
        </div>
      </div>

      {/* Section Navigation Dots */}
      <div className="mt-4">
        <div className="flex justify-center space-x-1">
          {sections.map((section, index) => {
            const isActive = section.id === currentSection.id;
            const isCompleted = currentQuestionNumber > section.endQuestion;
            const isUpcoming = currentQuestionNumber < section.startQuestion;
            
            return (
              <div
                key={section.id}
                className={`w-2 h-2 rounded-full transition-all duration-300 ${
                  isActive 
                    ? `${currentSection.color.replace('text-', 'bg-')} scale-125` 
                    : isCompleted 
                    ? 'bg-green-400' 
                    : isUpcoming 
                    ? 'bg-gray-300' 
                    : 'bg-gray-400'
                }`}
                title={section.title}
              />
            );
          })}
        </div>
      </div>

      {/* Next Section Preview */}
      {currentQuestionNumber < totalQuestions && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="text-xs text-gray-500 mb-2">Next up:</div>
          {(() => {
            const nextSection = sections.find(section => currentQuestionNumber < section.startQuestion);
            if (nextSection) {
              return (
                <div className="flex items-center space-x-2 text-xs text-gray-600">
                  <div className={`p-1 rounded ${nextSection.bgColor}`}>
                    <div className={nextSection.color}>
                      {nextSection.icon}
                    </div>
                  </div>
                  <span className="truncate">{nextSection.title}</span>
                </div>
              );
            }
            return null;
          })()}
        </div>
      )}
    </div>
  );
};

export default BusinessPlanProgressWidget;
