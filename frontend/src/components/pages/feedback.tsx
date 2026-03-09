"use client";

import { FeatherCheckCircle } from "@subframe/core";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Accordion } from "@/ui/components/Accordion";
import { Alert } from "@/ui/components/Alert";
import { Button } from "@/ui/components/Button";
import { Select } from "@/ui/components/Select";
import { TextArea } from "@/ui/components/TextArea";
import { TextField } from "@/ui/components/TextField";

export function FeedbackPage() {
  const { t } = useTranslation();
  const [category, setCategory] = useState("");
  const [subject, setSubject] = useState("");
  const [detail, setDetail] = useState("");
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const faqItems = [
    {
      question: t("feedback.faqItems.q1"),
      answer: t("feedback.faqItems.a1"),
    },
    {
      question: t("feedback.faqItems.q2"),
      answer: t("feedback.faqItems.a2"),
    },
    {
      question: t("feedback.faqItems.q3"),
      answer: t("feedback.faqItems.a3"),
    },
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
    setCategory("");
    setSubject("");
    setDetail("");
    setEmail("");
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-5xl mx-auto px-8 py-8">
        <h1 className="text-heading-2 font-heading-2 text-default-font">
          {t("feedback.pageTitle")}
        </h1>
        <p className="text-caption font-caption text-subtext-color mt-1">
          {t("feedback.pageSubtitle")}
        </p>

        <div className="mt-6 flex gap-8 items-start flex-col lg:flex-row">
          <div className="flex-1 w-full">
            {submitted && (
              <div className="mb-4">
                <Alert
                  variant="success"
                  icon={<FeatherCheckCircle />}
                  title={t("feedback.successTitle")}
                  description={t("feedback.successDescription")}
                />
              </div>
            )}

            <form
              onSubmit={handleSubmit}
              className="rounded-lg border border-border bg-card p-6 flex flex-col gap-5"
            >
              <Select
                label={t("feedback.category")}
                placeholder={t("feedback.categoryPlaceholder")}
                value={category}
                onValueChange={setCategory}
              >
                <Select.Item value="bug">{t("feedback.categoryBug")}</Select.Item>
                <Select.Item value="feature">{t("feedback.categoryFeature")}</Select.Item>
                <Select.Item value="general">{t("feedback.categoryGeneral")}</Select.Item>
                <Select.Item value="other">{t("feedback.categoryOther")}</Select.Item>
              </Select>

              <TextField label={t("feedback.subject")}>
                <TextField.Input
                  placeholder={t("feedback.subjectPlaceholder")}
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                />
              </TextField>

              <TextArea label={t("feedback.detail")}>
                <TextArea.Input
                  placeholder={t("feedback.detailPlaceholder")}
                  value={detail}
                  onChange={(e) => setDetail(e.target.value)}
                />
              </TextArea>

              <TextField label={t("feedback.email")} helpText={t("feedback.emailHelpText")}>
                <TextField.Input
                  placeholder="example@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </TextField>

              <div className="flex justify-end">
                <Button type="submit">{t("feedback.submit")}</Button>
              </div>
            </form>
          </div>

          <div className="w-full lg:w-80 shrink-0">
            <div className="rounded-lg border border-border bg-card p-6">
              <h2 className="text-body-bold font-body-bold text-default-font mb-4">
                {t("feedback.faq")}
              </h2>
              <div className="flex flex-col gap-2">
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
          </div>
        </div>
      </div>
    </div>
  );
}
