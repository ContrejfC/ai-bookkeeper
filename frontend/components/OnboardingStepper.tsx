'use client';

import React, { useState } from 'react';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  completed: boolean;
}

interface OnboardingStepperProps {
  currentStep: number;
  steps: OnboardingStep[];
  onStepClick?: (stepIndex: number) => void;
}

export function OnboardingStepper({ currentStep, steps, onStepClick }: OnboardingStepperProps) {
  return (
    <div className="w-full py-6">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => (
          <React.Fragment key={step.id}>
            {/* Step Circle */}
            <div className="flex flex-col items-center flex-1">
              <button
                onClick={() => onStepClick?.(index)}
                disabled={index > currentStep}
                className={`
                  w-12 h-12 rounded-full flex items-center justify-center font-semibold
                  transition-all duration-200
                  ${step.completed
                    ? 'bg-green-500 text-white'
                    : index === currentStep
                    ? 'bg-blue-600 text-white ring-4 ring-blue-200'
                    : index < currentStep
                    ? 'bg-blue-300 text-white'
                    : 'bg-gray-200 text-gray-500'}
                  ${index <= currentStep ? 'cursor-pointer hover:scale-110' : 'cursor-not-allowed'}
                `}
              >
                {step.completed ? '✓' : index + 1}
              </button>
              <div className="text-center mt-2">
                <p className={`text-sm font-medium ${index === currentStep ? 'text-blue-600' : 'text-gray-600'}`}>
                  {step.title}
                </p>
                <p className="text-xs text-gray-500 mt-1 max-w-[120px]">{step.description}</p>
              </div>
            </div>
            
            {/* Connector Line */}
            {index < steps.length - 1 && (
              <div className={`
                flex-1 h-1 mx-2 transition-all duration-200
                ${step.completed || index < currentStep ? 'bg-blue-500' : 'bg-gray-200'}
              `} />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

