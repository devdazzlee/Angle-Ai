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
      <div className="bg-white shadow-lg rounded-lg overflow-hidden border border-gray-100">
        <div className="p-4 border-b border-gray-100">
          <h3 className="text-lg font-semibold text-gray-800">Progress Overview</h3>
        </div>

        {/* Overall Progress */}
        <div className="p-4 border-b border-gray-100">
          <div className="mb-2 flex justify-between items-center">
            <span className="text-sm font-medium text-gray-600">Overall Progress</span>
            <span className="text-sm font-medium text-gray-600">
              {currentProgress.answered} / {currentProgress.total}
            </span>
          </div>
          <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-teal-500 rounded-full transition-all duration-300"
              style={{ width: `${currentProgress.percent}%` }}
            />
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
