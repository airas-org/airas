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
import { Button, IconWithBackground, Stepper } from "@/ui";

interface OnboardingOverlayProps {
  onComplete: () => void;
}

const steps = [
  {
    title: "ようこそ AIRASへ",
    description:
      "AIRASは研究者のための自動研究支援プラットフォームです。仮説の立案から実験の実行、論文の執筆まで、研究プロセス全体をAIが支援します。",
    icon: <FeatherZap />,
  },
  {
    title: "検証ワークフロー",
    description:
      "検証方針の立案から実験実行、論文執筆までを一貫して支援します。各フェーズをステップバイステップで進めることができます。",
    icons: [
      { icon: <FeatherSearch />, label: "方針立案" },
      { icon: <FeatherCode />, label: "実験実行" },
      { icon: <FeatherFileText />, label: "論文執筆" },
    ],
  },
  {
    title: "自動研究",
    description:
      "AIが自動的に研究を進めるモードも利用可能です。Topic-DrivenとHypothesis-Drivenの2つのモードがあります。",
    modes: [
      {
        icon: <FeatherSearch />,
        name: "Topic-Driven",
        desc: "トピックからAIが仮説を生成",
      },
      {
        icon: <FeatherZap />,
        name: "Hypothesis-Driven",
        desc: "仮説を元にAIが検証を実行",
      },
    ],
  },
  {
    title: "準備完了",
    description: "さっそく始めましょう！",
    icon: <FeatherRocket />,
  },
] as const;

export function OnboardingOverlay({ onComplete }: OnboardingOverlayProps) {
  const [currentStep, setCurrentStep] = useState(0);

  const isLastStep = currentStep === steps.length - 1;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="relative flex w-full max-w-2xl flex-col gap-8 rounded-2xl bg-default-background p-8 shadow-xl">
        <button
          type="button"
          onClick={onComplete}
          className="absolute top-4 right-4 cursor-pointer border-none bg-transparent text-body font-body text-subtext-color hover:text-default-font"
        >
          スキップ
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
          <StepContent step={currentStep} />
        </div>

        <div className="flex items-center justify-between">
          <div>
            {currentStep > 0 && (
              <Button
                variant="neutral-secondary"
                icon={<FeatherArrowLeft />}
                onClick={() => setCurrentStep((s) => s - 1)}
              >
                戻る
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
            {isLastStep ? "始める" : "次へ"}
          </Button>
        </div>
      </div>
    </div>
  );
}

function StepContent({ step }: { step: number }) {
  const data = steps[step];

  if ("icons" in data) {
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

  if ("modes" in data) {
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
