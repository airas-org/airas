"use client";

import { FeatherBookOpen, FeatherGitBranch, FeatherPlay, FeatherSettings } from "@subframe/core";
import { useTranslation } from "react-i18next";
import { Accordion } from "@/ui/components/Accordion";

export function HelpPage() {
  const { t } = useTranslation();

  const gettingStartedSteps = [
    {
      title: t("help.gettingStartedSteps.step1.title"),
      description: t("help.gettingStartedSteps.step1.description"),
    },
    {
      title: t("help.gettingStartedSteps.step2.title"),
      description: t("help.gettingStartedSteps.step2.description"),
    },
    {
      title: t("help.gettingStartedSteps.step3.title"),
      description: t("help.gettingStartedSteps.step3.description"),
    },
    {
      title: t("help.gettingStartedSteps.step4.title"),
      description: t("help.gettingStartedSteps.step4.description"),
    },
  ];

  const featureGuides = [
    {
      icon: <FeatherPlay />,
      title: t("help.featureGuides.verificationWorkflow.title"),
      items: [
        {
          question: t("help.featureGuides.verificationWorkflow.q1"),
          answer: t("help.featureGuides.verificationWorkflow.a1"),
        },
        {
          question: t("help.featureGuides.verificationWorkflow.q2"),
          answer: t("help.featureGuides.verificationWorkflow.a2"),
        },
      ],
    },
    {
      icon: <FeatherGitBranch />,
      title: t("help.featureGuides.autonomousResearch.title"),
      items: [
        {
          question: t("help.featureGuides.autonomousResearch.q1"),
          answer: t("help.featureGuides.autonomousResearch.a1"),
        },
        {
          question: t("help.featureGuides.autonomousResearch.q2"),
          answer: t("help.featureGuides.autonomousResearch.a2"),
        },
      ],
    },
    {
      icon: <FeatherSettings />,
      title: t("help.featureGuides.integration.title"),
      items: [
        {
          question: t("help.featureGuides.integration.q1"),
          answer: t("help.featureGuides.integration.a1"),
        },
        {
          question: t("help.featureGuides.integration.q2"),
          answer: t("help.featureGuides.integration.a2"),
        },
      ],
    },
    {
      icon: <FeatherBookOpen />,
      title: t("help.featureGuides.paper.title"),
      items: [
        {
          question: t("help.featureGuides.paper.q1"),
          answer: t("help.featureGuides.paper.a1"),
        },
        {
          question: t("help.featureGuides.paper.q2"),
          answer: t("help.featureGuides.paper.a2"),
        },
      ],
    },
  ];

  const faqItems = [
    { question: t("help.faqItems.q1"), answer: t("help.faqItems.a1") },
    { question: t("help.faqItems.q2"), answer: t("help.faqItems.a2") },
    { question: t("help.faqItems.q3"), answer: t("help.faqItems.a3") },
  ];

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-5xl mx-auto px-8 py-8">
        <h1 className="text-heading-2 font-heading-2 text-default-font">{t("help.title")}</h1>
        <p className="text-caption font-caption text-subtext-color mt-1">{t("help.subtitle")}</p>

        <div className="mt-6 space-y-6">
          {/* Getting Started */}
          <div className="rounded-lg border border-border bg-card p-5">
            <h2 className="text-body-bold font-body-bold text-default-font mb-3">
              {t("help.gettingStarted")}
            </h2>
            <div className="grid gap-3 md:grid-cols-2">
              {gettingStartedSteps.map((step) => (
                <div key={step.title} className="rounded-md bg-neutral-50 p-3">
                  <p className="text-sm font-semibold text-default-font">{step.title}</p>
                  <p className="text-caption font-caption text-subtext-color mt-1">
                    {step.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Feature Guides */}
          {featureGuides.map((guide) => (
            <div key={guide.title} className="rounded-lg border border-border bg-card p-5">
              <h2 className="text-body-bold font-body-bold text-default-font mb-3 flex items-center gap-2">
                <span className="text-subtext-color">{guide.icon}</span>
                {guide.title}
              </h2>
              <div className="flex flex-col gap-1">
                {guide.items.map((item) => (
                  <Accordion
                    key={item.question}
                    trigger={
                      <div className="flex w-full items-center justify-between rounded-md px-3 py-2 hover:bg-neutral-50">
                        <span className="text-body font-body text-default-font pr-2">
                          {item.question}
                        </span>
                        <Accordion.Chevron />
                      </div>
                    }
                  >
                    <p className="text-caption font-caption text-subtext-color px-3 pb-2 leading-relaxed">
                      {item.answer}
                    </p>
                  </Accordion>
                ))}
              </div>
            </div>
          ))}

          {/* FAQ */}
          <div className="rounded-lg border border-border bg-card p-5">
            <h2 className="text-body-bold font-body-bold text-default-font mb-3">
              {t("help.faq")}
            </h2>
            <div className="flex flex-col gap-1">
              {faqItems.map((item) => (
                <Accordion
                  key={item.question}
                  trigger={
                    <div className="flex w-full items-center justify-between rounded-md px-3 py-2 hover:bg-neutral-50">
                      <span className="text-body font-body text-default-font pr-2">
                        {item.question}
                      </span>
                      <Accordion.Chevron />
                    </div>
                  }
                >
                  <p className="text-caption font-caption text-subtext-color px-3 pb-2 leading-relaxed">
                    {item.answer}
                  </p>
                </Accordion>
              ))}
            </div>
          </div>

          {/* External Links */}
          <div className="flex gap-3">
            <a
              href="https://airas-org.github.io/airas/"
              target="_blank"
              rel="noreferrer"
              className="flex-1 rounded-lg border border-border bg-card p-4 hover:bg-neutral-50 transition-colors"
            >
              <p className="text-sm font-semibold text-default-font">{t("help.links.docs")}</p>
              <p className="text-caption font-caption text-subtext-color mt-1">
                {t("help.links.docsDesc")}
              </p>
            </a>
            <a
              href="https://discord.gg/uDmkgKfkes"
              target="_blank"
              rel="noreferrer"
              className="flex-1 rounded-lg border border-border bg-card p-4 hover:bg-neutral-50 transition-colors"
            >
              <p className="text-sm font-semibold text-default-font">{t("help.links.discord")}</p>
              <p className="text-caption font-caption text-subtext-color mt-1">
                {t("help.links.discordDesc")}
              </p>
            </a>
            <a
              href="https://github.com/airas-org/airas"
              target="_blank"
              rel="noreferrer"
              className="flex-1 rounded-lg border border-border bg-card p-4 hover:bg-neutral-50 transition-colors"
            >
              <p className="text-sm font-semibold text-default-font">{t("help.links.github")}</p>
              <p className="text-caption font-caption text-subtext-color mt-1">
                {t("help.links.githubDesc")}
              </p>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
