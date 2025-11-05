'use client';

/**
 * Stepper Component
 * ==================
 * 4-step progress indicator
 */

interface StepperProps {
  currentStep: number; // 1-4
  steps: string[];
}

export function Stepper({ currentStep, steps }: StepperProps) {
  return (
    <div className="w-full py-6">
      <div className="flex items-center justify-between max-w-3xl mx-auto">
        {steps.map((step, index) => {
          const stepNum = index + 1;
          const isActive = stepNum === currentStep;
          const isComplete = stepNum < currentStep;
          
          return (
            <div key={stepNum} className="flex items-center flex-1">
              {/* Step circle */}
              <div className="flex flex-col items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                    isComplete
                      ? 'bg-emerald-600 text-white'
                      : isActive
                      ? 'bg-emerald-600 text-white ring-4 ring-emerald-200'
                      : 'bg-gray-200 text-gray-500'
                  }`}
                >
                  {isComplete ? '✓' : stepNum}
                </div>
                <div
                  className={`mt-2 text-sm font-medium ${
                    isActive ? 'text-emerald-600' : 'text-gray-500'
                  }`}
                >
                  {step}
                </div>
              </div>
              
              {/* Connector line */}
              {index < steps.length - 1 && (
                <div
                  className={`flex-1 h-1 mx-4 ${
                    isComplete ? 'bg-emerald-600' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

