import { useTranslation } from "react-i18next";

export function ReproductionPage() {
  const { t } = useTranslation();
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center space-y-3">
        <h1 className="text-heading-2 font-heading-2 text-default-font">
          {t("reproduction.title")}
        </h1>
        <p className="text-body font-body text-subtext-color">{t("reproduction.comingSoon")}</p>
      </div>
    </div>
  );
}
