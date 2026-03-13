import { useTranslation } from "react-i18next";

export function ReceiptsPage() {
  const { t } = useTranslation();
  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-2xl mx-auto px-8 py-8">
        <h1 className="text-heading-2 font-heading-2 text-default-font">{t("receipts.title")}</h1>
        <p className="text-caption font-caption text-subtext-color mt-1">
          {t("receipts.subtitle")}
        </p>
        <div className="mt-6 rounded-lg border border-border bg-card p-5 text-center text-body font-body text-subtext-color">
          {t("receipts.empty")}
        </div>
      </div>
    </div>
  );
}
