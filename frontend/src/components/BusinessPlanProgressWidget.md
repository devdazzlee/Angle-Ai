# Business Plan Progress Widget

A beautiful, animated progress tracking widget specifically designed for the Business Plan phase of the Angel AI assistant.

## Features

### 🎯 Section Tracking
- **9 Business Plan Sections**: Each section corresponds to a specific area of business planning
- **Dynamic Section Detection**: Automatically identifies the current section based on question number
- **Section Progress**: Shows progress within the current section (e.g., "2 of 4 questions")

### 📊 Progress Visualization
- **Linear Progress Bar**: Shows section completion percentage
- **Circular Progress Indicator**: Displays overall business plan completion
- **Section Navigation Dots**: Visual indicators for all sections with status (completed, current, upcoming)

### 🎨 Beautiful UI
- **Color-coded Sections**: Each section has its own color theme and icon
- **Smooth Animations**: Fade and scale transitions when switching sections
- **Responsive Design**: Works perfectly on desktop and mobile
- **Minimal & Clean**: Matches the existing sidebar theme

### 📱 Smart Integration
- **Phase-specific**: Only appears during the BUSINESS_PLAN phase
- **Real-time Updates**: Automatically updates as users answer questions
- **Fallback Handling**: Gracefully handles edge cases and unexpected question numbers

## Section Mapping

Based on the business plan structure from `constant.py`:

1. **Business Foundation** (Questions 1-4)
   - Business name, tagline, problem, unique value proposition

2. **Product/Service Details** (Questions 5-8)
   - Core product description, features, IP, development timeline

3. **Market Research** (Questions 9-12)
   - Target market, market size, competitors, alternatives

4. **Location & Operations** (Questions 13-17)
   - Business location, facilities, staffing, suppliers

5. **Financial Planning** (Questions 18-25)
   - Pricing, sales projections, costs, funding, financial management

6. **Marketing & Sales** (Questions 26-31)
   - Marketing channels, sales process, customer acquisition, partnerships

7. **Legal & Compliance** (Questions 32-38)
   - Business structure, licenses, insurance, contracts, taxes

8. **Growth & Scaling** (Questions 39-42)
   - Milestones, expansion plans, partnerships, scaling strategies

9. **Risk Management** (Questions 43-46)
   - Risk identification, contingency plans, concerns, final considerations

## Usage

```tsx
import BusinessPlanProgressWidget from './BusinessPlanProgressWidget';

<BusinessPlanProgressWidget
  currentQuestionNumber={currentQuestionNumber}
  totalQuestions={totalQuestions}
  className="shadow-lg"
/>
```

## Props

- `currentQuestionNumber: number` - The current question number (1-based)
- `totalQuestions: number` - Total number of business plan questions
- `className?: string` - Additional CSS classes for styling

## Integration

The widget is automatically integrated into the right sidebar via the `QuestionNavigator` component and only displays during the `BUSINESS_PLAN` phase.

## Animations

- **Section Transitions**: 300ms scale and opacity animations
- **Progress Updates**: Smooth 500ms progress bar animations
- **Hover Effects**: Subtle scale effects on interactive elements

## Accessibility

- **Semantic HTML**: Proper heading structure and ARIA labels
- **Color Contrast**: High contrast colors for readability
- **Screen Reader Support**: Descriptive text for progress indicators



