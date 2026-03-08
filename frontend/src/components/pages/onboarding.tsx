import {
  FeatherArrowLeft,
  FeatherArrowRight,
  FeatherCode,
  FeatherFileText,
  FeatherRocket,
  FeatherSearch,
  FeatherZap,
} from "@subframe/core";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button, IconWithBackground, Stepper } from "@/ui";

interface OnboardingOverlayProps {
  onComplete: () => void;
}

export function OnboardingOverlay({ onComplete }: OnboardingOverlayProps) {
  const { t } = useTranslation();
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    {
      title: t("onboarding.steps.welcome.title"),
      description: t("onboarding.steps.welcome.description"),
      icon: <FeatherZap />,
    },
    {
      title: t("onboarding.steps.workflow.title"),
      description: t("onboarding.steps.workflow.description"),
      icons: [
        { icon: <FeatherSearch />, label: t("onboarding.steps.workflow.planLabel") },
        { icon: <FeatherCode />, label: t("onboarding.steps.workflow.experimentLabel") },
        { icon: <FeatherFileText />, label: t("onboarding.steps.workflow.paperLabel") },
      ],
    },
    {
      title: t("onboarding.steps.autonomous.title"),
      description: t("onboarding.steps.autonomous.description"),
      modes: [
        {
          icon: <FeatherSearch />,
          name: "Topic-Driven",
          desc: t("onboarding.steps.autonomous.topicDrivenDesc"),
        },
        {
          icon: <FeatherZap />,
          name: "Hypothesis-Driven",
          desc: t("onboarding.steps.autonomous.hypothesisDrivenDesc"),
        },
      ],
    },
    {
      title: t("onboarding.steps.ready.title"),
      description: t("onboarding.steps.ready.description"),
      icon: <FeatherRocket />,
    },
  ];

  const isLastStep = currentStep === steps.length - 1;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="relative flex w-full max-w-2xl flex-col gap-8 rounded-2xl bg-default-background p-8 shadow-xl">
        <button
          type="button"
          onClick={onComplete}
          className="absolute top-4 right-4 cursor-pointer border-none bg-transparent text-body font-body text-subtext-color hover:text-default-font"
        >
          {t("onboarding.skip")}
        </button>

        <Stepper>
          {steps.map((step, i) => (
            <Stepper.Step
              key={step.title}
              stepNumber={String(i + 1)}
              label={step.title}
              variant={i < currentStep ? "completed" : i === currentStep ? "active" : "default"}
              firstStep={i === 0}
              lastStep={i === steps.length - 1}
            />
          ))}
        </Stepper>

        <div className="flex min-h-[200px] flex-col items-center justify-center gap-6 text-center">
          <StepContent step={currentStep} steps={steps} />
        </div>

        <div className="flex items-center justify-between">
          <div>
            {currentStep > 0 && (
              <Button
                variant="neutral-secondary"
                icon={<FeatherArrowLeft />}
                onClick={() => setCurrentStep((s) => s - 1)}
              >
                {t("onboarding.back")}
              </Button>
            )}
          </div>
          <Button
            icon={isLastStep ? <FeatherRocket /> : undefined}
            iconRight={isLastStep ? undefined : <FeatherArrowRight />}
            onClick={() => {
              if (isLastStep) {
                onComplete();
              } else {
                setCurrentStep((s) => s + 1);
              }
            }}
          >
            {isLastStep ? t("onboarding.start") : t("onboarding.next")}
          </Button>
        </div>
      </div>
    </div>
  );
}

type Step = {
  title: string;
  description: string;
  icon?: React.ReactNode;
  icons?: { icon: React.ReactNode; label: string }[];
  modes?: { icon: React.ReactNode; name: string; desc: string }[];
};

function StepContent({ step, steps }: { step: number; steps: Step[] }) {
  const data = steps[step];

  if (data.icons) {
    return (
      <>
        <h2 className="text-heading-2 font-heading-2 text-default-font">{data.title}</h2>
        <p className="text-body font-body text-subtext-color max-w-md">{data.description}</p>
        <div className="flex items-center gap-8">
          {data.icons.map((item) => (
            <div key={item.label} className="flex flex-col items-center gap-2">
              <IconWithBackground variant="brand" size="large" icon={item.icon} />
              <span className="text-caption-bold font-caption-bold text-default-font">
                {item.label}
              </span>
            </div>
          ))}
        </div>
      </>
    );
  }

  if (data.modes) {
    return (
      <>
        <h2 className="text-heading-2 font-heading-2 text-default-font">{data.title}</h2>
        <p className="text-body font-body text-subtext-color max-w-md">{data.description}</p>
        <div className="flex gap-6">
          {data.modes.map((mode) => (
            <div
              key={mode.name}
              className="flex flex-col items-center gap-3 rounded-xl border border-neutral-border bg-neutral-50 p-5"
            >
              <IconWithBackground variant="brand" size="large" icon={mode.icon} />
              <span className="text-body-bold font-body-bold text-default-font">{mode.name}</span>
              <span className="text-caption font-caption text-subtext-color">{mode.desc}</span>
            </div>
          ))}
        </div>
      </>
    );
  }

  const isLastStep = step === steps.length - 1;

  return (
    <>
      <IconWithBackground
        variant={isLastStep ? "success" : "brand"}
        size="x-large"
        icon={data.icon}
      />
      <div className="flex flex-col gap-2">
        <h2 className="text-heading-2 font-heading-2 text-default-font">{data.title}</h2>
        <p className="text-body font-body text-subtext-color max-w-md">{data.description}</p>
      </div>
    </>
  );
}
