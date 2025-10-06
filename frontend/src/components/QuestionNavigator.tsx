import React from 'react';
import BusinessPlanProgressWidget from './BusinessPlanProgressWidget';

interface Question {
  id: string;
  phase: string;
  number: number;
  title: string;
  completed: boolean;
}

interface QuestionNavigatorProps {
  questions: Question[];
  currentPhase: string;
  onQuestionSelect: (questionId: string) => void;
  currentProgress: {
    phase: string;
    answered: number;
    total: number;
    percent: number;
    combined?: boolean;
    phase_breakdown?: {
      kyc_completed: number;
      kyc_total: number;
      bp_completed: number;
      bp_total: number;
    };
  };
  onEditPlan?: () => void;
  onUploadPlan?: (file: File) => void;
}

const phaseColors = {
  KYC: 'text-blue-600 bg-blue-50 border-blue-200',
  BUSINESS_PLAN: 'text-purple-600 bg-purple-50 border-purple-200',
  ROADMAP: 'text-teal-600 bg-teal-50 border-teal-200',
  IMPLEMENTATION: 'text-green-600 bg-green-50 border-green-200'
};

const phaseNames = {
  KYC: 'Getting to Know You',
  BUSINESS_PLAN: 'Business Plan',
  ROADMAP: 'Roadmap',
  IMPLEMENTATION: 'Implementation'
};

const QuestionNavigator: React.FC<QuestionNavigatorProps> = ({
  questions,
  currentPhase,
  onQuestionSelect,
  currentProgress,
  onEditPlan,
  onUploadPlan
}) => {
  // Group questions by phase
  const questionsByPhase = questions.reduce((acc, question) => {
    if (!acc[question.phase]) {
      acc[question.phase] = [];
    }
    acc[question.phase].push(question);
    return acc;
  }, {} as Record<string, Question[]>);

  return (
    <div className="w-80 space-y-4">
      {/* Business Plan Progress Widget - Only show during BUSINESS_PLAN phase */}
      {currentPhase === 'BUSINESS_PLAN' && (
        <BusinessPlanProgressWidget
          currentQuestionNumber={currentProgress.answered + 1}
          totalQuestions={currentProgress.total}
          className="shadow-lg"
        />
      )}

      {/* Original Progress Overview - Show for all phases */}
      <div className="bg-white shadow-xl rounded-xl overflow-hidden border border-gray-100 hover:shadow-2xl transition-all duration-300 hover:scale-[1.02]">
        <div className="p-4 border-b border-gray-100">
          <h3 className="text-lg font-semibold text-gray-800">Progress Overview</h3>
        </div>

        {/* Overall Progress */}
        <div className="p-4 border-b border-gray-100 bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50">
          <div className="mb-3 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Overall Progress</span>
            </div>
            <div className="flex items-center gap-1.5 bg-white px-2.5 py-1 rounded-lg shadow-sm border border-gray-200">
              <span className="text-lg font-bold text-gray-900">
                {currentProgress.answered}
              </span>
              <span className="text-sm text-gray-400 font-medium">/</span>
              <span className="text-lg font-bold text-gray-700">
                {currentProgress.total}
              </span>
            </div>
          </div>
          
          {/* Compact Progress Bar */}
          <div className="relative">
            <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden shadow-inner border border-gray-200">
              <div
                className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-teal-500 rounded-full transition-all duration-1000 ease-out relative overflow-hidden"
                style={{ width: `${currentProgress.percent}%` }}
              >
                {/* Shimmer Effect */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-40 animate-shimmer"></div>
              </div>
            </div>
            
            {/* Progress Percentage */}
            <div className="mt-2 text-center">
              <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-teal-600 bg-clip-text text-transparent animate-gradient">
                {Math.round(currentProgress.percent)}%
              </span>
              <div className="text-xs text-gray-500 mt-0.5 font-medium uppercase tracking-wide">
                Complete
              </div>
            </div>
            
            {/* Compact Progress Milestones */}
            <div className="mt-3 flex justify-between">
              <div className="flex items-center gap-1.5 bg-blue-50 px-2 py-1 rounded-lg border border-blue-200">
                <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                <span className="text-xs font-medium text-blue-700 uppercase tracking-wide">KYC</span>
              </div>
              <div className="flex items-center gap-1.5 bg-purple-50 px-2 py-1 rounded-lg border border-purple-200">
                <div className="w-1.5 h-1.5 bg-purple-500 rounded-full"></div>
                <span className="text-xs font-medium text-purple-700 uppercase tracking-wide">BP</span>
              </div>
            </div>
          </div>
        </div>

        {/* Sections by Phase */}
        

        {/* File Upload Section */}
        <div className="p-4 border-t border-gray-100">
          <div className="flex flex-col gap-3">
            <label
              htmlFor="plan-upload"
              className="flex items-center justify-center px-4 py-2 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-teal-500 transition-colors"
            >
              <span className="text-sm text-gray-600">Upload Business Plan</span>
              <input
                id="plan-upload"
                type="file"
                className="hidden"
                accept=".pdf,.doc,.docx"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    console.log('File selected:', file);
                    if (onUploadPlan) {
                      onUploadPlan(file);
                    }
                  }
                }}
              />
            </label>
            
            {currentPhase === 'BUSINESS_PLAN' && (
              <button
                className="px-4 py-2 bg-teal-600 text-white rounded-lg text-sm hover:bg-teal-700 transition-colors"
                onClick={() => {
                  console.log('Edit plan clicked');
                  if (onEditPlan) {
                    onEditPlan();
                  }
                }}
              >
                Edit Business Plan
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuestionNavigator;
