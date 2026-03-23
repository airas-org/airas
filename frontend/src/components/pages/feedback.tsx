import { FeatherAlertTriangle, FeatherCheckCircle } from "@subframe/core";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { FeedbackService } from "@/lib/api/services/FeedbackService";
import { Accordion } from "@/ui/components/Accordion";
import { Alert } from "@/ui/components/Alert";
import { Button } from "@/ui/components/Button";
import { Select } from "@/ui/components/Select";
import { TextArea } from "@/ui/components/TextArea";
import { TextField } from "@/ui/components/TextField";

const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

const MAX_SUBJECT_LENGTH = 255;
const MAX_DETAIL_LENGTH = 5000;

type Category = "bug" | "feature" | "general" | "other";

interface ValidationErrors {
  category?: string;
  subject?: string;
  detail?: string;
  email?: string;
}

export function FeedbackPage() {
  const { t } = useTranslation();
  const [category, setCategory] = useState<Category | null>(null);
  const [subject, setSubject] = useState("");
  const [detail, setDetail] = useState("");
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errors, setErrors] = useState<ValidationErrors>({});

  const resetForm = () => {
    setCategory(null);
    setSubject("");
    setDetail("");
    setEmail("");
    setErrors({});
  };

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

  const validate = (): ValidationErrors => {
    const v: ValidationErrors = {};
    const trimmedSubject = subject.trim();
    const trimmedDetail = detail.trim();
    if (!category) v.category = t("feedback.validation.categoryRequired");
    if (!trimmedSubject) v.subject = t("feedback.validation.subjectRequired");
    else if (trimmedSubject.length > MAX_SUBJECT_LENGTH)
      v.subject = t("feedback.validation.subjectTooLong");
    if (!trimmedDetail) v.detail = t("feedback.validation.detailRequired");
    else if (trimmedDetail.length > MAX_DETAIL_LENGTH)
      v.detail = t("feedback.validation.detailTooLong");
    if (email && !EMAIL_REGEX.test(email)) v.email = t("feedback.validation.emailInvalid");
    return v;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;
    setError(null);
    setSubmitted(false);

    const v = validate();
    setErrors(v);
    if (Object.keys(v).length > 0) return;

    setSubmitting(true);
    try {
      await FeedbackService.createFeedbackAirasV1FeedbackPost({
        category: category!,
        subject: subject.trim(),
        detail: detail.trim(),
        email: email.trim() || null,
      });
      setSubmitted(true);
      window.scrollTo({ top: 0, behavior: "smooth" });
      resetForm();
    } catch (e) {
      console.error(e);
      setError(e instanceof Error ? e.message : t("feedback.submitError"));
    } finally {
      setSubmitting(false);
    }
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

            {error && (
              <div className="mb-4">
                <Alert
                  variant="error"
                  icon={<FeatherAlertTriangle />}
                  title={t("feedback.submitError")}
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
                value={category ?? ""}
                onValueChange={(v) => {
                  setCategory(v as Category);
                  setErrors((prev) => ({ ...prev, category: undefined }));
                }}
                error={!!errors.category}
                helpText={errors.category}
              >
                <Select.Item value="bug">{t("feedback.categoryBug")}</Select.Item>
                <Select.Item value="feature">{t("feedback.categoryFeature")}</Select.Item>
                <Select.Item value="general">{t("feedback.categoryGeneral")}</Select.Item>
                <Select.Item value="other">{t("feedback.categoryOther")}</Select.Item>
              </Select>

              <TextField
                label={t("feedback.subject")}
                error={!!errors.subject}
                helpText={errors.subject}
              >
                <TextField.Input
                  placeholder={t("feedback.subjectPlaceholder")}
                  value={subject}
                  onChange={(e) => {
                    setSubject(e.target.value);
                    setErrors((prev) => ({ ...prev, subject: undefined }));
                  }}
                />
              </TextField>

              <TextArea
                label={t("feedback.detail")}
                error={!!errors.detail}
                helpText={errors.detail}
              >
                <TextArea.Input
                  placeholder={t("feedback.detailPlaceholder")}
                  value={detail}
                  onChange={(e) => {
                    setDetail(e.target.value);
                    setErrors((prev) => ({ ...prev, detail: undefined }));
                  }}
                />
              </TextArea>

              <TextField
                label={t("feedback.email")}
                helpText={errors.email || t("feedback.emailHelpText")}
                error={!!errors.email}
              >
                <TextField.Input
                  placeholder="example@email.com"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    setErrors((prev) => ({ ...prev, email: undefined }));
                  }}
                />
              </TextField>

              <div className="flex justify-end">
                <Button type="submit" disabled={submitting}>
                  {submitting && <Loader2 className="h-3 w-3 animate-spin" />}
                  {submitting ? t("feedback.submitting") : t("feedback.submit")}
                </Button>
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
