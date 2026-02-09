"use client";

import { useState } from "react";

/**
 * InterviewAI Homepage Component
 * 
 * Main landing page for the InterviewAI application showcasing features
 * and providing quick access to core functionality.
 * 
 * Note: BUG #5 - The useState hook for 'selectedFeature' is declared but
 * the setter is called with a potentially undefined value in handleFeatureClick.
 * This could cause issues if the feature index is out of bounds.
 */
export default function HomePage() {
  // BUG #5: useState for selectedFeature but no proper bounds checking
  // When features array changes or is empty, this could cause issues
  const [selectedFeature, setSelectedFeature] = useState<number>();

  const features = [
    {
      title: "AI-Powered Interviews",
      description: "Conduct automated pre-selection interviews using advanced AI",
      icon: "🤖",
    },
    {
      title: "Smart Transcription",
      description: "Accurate speech-to-text conversion for interview responses",
      icon: "🎙️",
    },
    {
      title: "Intelligent Evaluation",
      description: "Get detailed candidate assessments with scoring and insights",
      icon: "📊",
    },
  ];

  /**
   * Handle feature card click
   * BUG #5: No validation that idx is within bounds of features array
   */
  const handleFeatureClick = (idx: number) => {
    // BUG: Should validate: if (idx >= 0 && idx < features.length)
    setSelectedFeature(idx);
    const feature = features[idx]; // Could be undefined if idx is out of bounds
    console.log(`Selected feature: ${feature.title}`); // Will crash if feature is undefined
  };

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <section className="space-y-4" aria-labelledby="hero-heading">
        <h1
          id="hero-heading"
          className="text-4xl md:text-5xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent"
        >
          InterviewAI
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl">
          AI‑powered pre‑selection interviews for any role.
          Streamline your hiring process with intelligent automation.
        </p>

        {/* Call to Action Buttons */}
        <div className="flex flex-wrap gap-4 pt-4">
          <button
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            aria-label="Start a new interview"
          >
            Start Interview
          </button>
          <button
            className="px-6 py-3 border border-gray-300 rounded-lg font-medium hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
            aria-label="View documentation"
          >
            View Documentation
          </button>
        </div>
      </section>

      {/* Features Section */}
      <section className="space-y-6" aria-labelledby="features-heading">
        <h2
          id="features-heading"
          className="text-2xl font-semibold tracking-tight"
        >
          Key Features
        </h2>

        <div className="grid md:grid-cols-3 gap-6">
          {features.map((feature, idx) => (
            <article
              key={idx}
              onClick={() => handleFeatureClick(idx)}
              className={`p-6 border rounded-lg hover:shadow-lg transition-all cursor-pointer ${selectedFeature === idx
                  ? "border-blue-500 bg-blue-50 dark:bg-blue-950"
                  : "border-gray-200 hover:border-gray-300"
                }`}
              role="button"
              tabIndex={0}
              aria-pressed={selectedFeature === idx}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  handleFeatureClick(idx);
                }
              }}
            >
              <div className="text-4xl mb-4" aria-hidden="true">
                {feature.icon}
              </div>
              <h3 className="text-lg font-semibold mb-2">
                {feature.title}
              </h3>
              <p className="text-muted-foreground">
                {feature.description}
              </p>
            </article>
          ))}
        </div>

        {selectedFeature !== undefined && (
          <div
            className="mt-4 p-4 bg-blue-100 dark:bg-blue-900 rounded-lg"
            role="status"
            aria-live="polite"
          >
            <p className="text-sm">
              You selected: <strong>{features[selectedFeature]?.title || "Unknown"}</strong>
            </p>
          </div>
        )}
      </section>

      {/* Statistics Section */}
      <section className="grid md:grid-cols-3 gap-6" aria-label="Statistics">
        <div className="text-center p-6 border rounded-lg">
          <div className="text-3xl font-bold text-blue-600">1000+</div>
          <div className="text-sm text-muted-foreground mt-1">Interviews Conducted</div>
        </div>
        <div className="text-center p-6 border rounded-lg">
          <div className="text-3xl font-bold text-purple-600">95%</div>
          <div className="text-sm text-muted-foreground mt-1">Accuracy Rate</div>
        </div>
        <div className="text-center p-6 border rounded-lg">
          <div className="text-3xl font-bold text-green-600">50%</div>
          <div className="text-sm text-muted-foreground mt-1">Time Saved</div>
        </div>
      </section>
    </div>
  );
}
