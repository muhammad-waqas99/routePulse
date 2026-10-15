export const optimizationStages = [
  {
    id: "loading-scenario",
    title: "Load scenario",
    description: "Preparing network and initial conditions.",
  },
  {
    id: "optimizing",
    title: "Optimize schedule",
    description: "Generating a candidate transportation plan.",
  },
  {
    id: "validating",
    title: "Validate constraints",
    description: "Checking operational constraints.",
  },
  {
    id: "evaluating",
    title: "Evaluate plan",
    description: "Calculating simulated evaluation metrics.",
  },
] as const;
