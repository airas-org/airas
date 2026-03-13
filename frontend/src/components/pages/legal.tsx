"use client";

import { useState } from "react";
import { useTranslation } from "react-i18next";

type Tab = "terms" | "privacy";

export function LegalPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<Tab>("terms");

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-8 py-8">
        <h1 className="text-heading-2 font-heading-2 text-default-font">{t("legal.pageTitle")}</h1>
        <p className="text-caption font-caption text-subtext-color mt-1">
          {t("legal.pageSubtitle")}
        </p>

        <div className="mt-6 flex gap-2">
          <button
            type="button"
            onClick={() => setActiveTab("terms")}
            className={`rounded-md px-4 py-2 text-body-bold font-body-bold transition-colors ${
              activeTab === "terms"
                ? "bg-brand-600 text-white"
                : "bg-neutral-100 text-default-font hover:bg-neutral-200"
            }`}
          >
            {t("legal.tabs.terms")}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("privacy")}
            className={`rounded-md px-4 py-2 text-body-bold font-body-bold transition-colors ${
              activeTab === "privacy"
                ? "bg-brand-600 text-white"
                : "bg-neutral-100 text-default-font hover:bg-neutral-200"
            }`}
          >
            {t("legal.tabs.privacy")}
          </button>
        </div>

        <div className="mt-6 rounded-lg border border-border bg-card p-6">
          {activeTab === "terms" ? <TermsContent /> : <PrivacyContent />}
        </div>
      </div>
    </div>
  );
}

function TermsContent() {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col gap-6">
      <p className="text-caption font-caption text-subtext-color">{t("legal.terms.lastUpdated")}</p>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">
          {t("legal.terms.overview.title")}
        </h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          {t("legal.terms.overview.content")}
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">
          {t("legal.terms.usage.title")}
        </h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          {t("legal.terms.usage.content")}
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">
          {t("legal.terms.account.title")}
        </h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          {t("legal.terms.account.content")}
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">
          {t("legal.terms.ip.title")}
        </h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          {t("legal.terms.ip.content")}
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">
          {t("legal.terms.disclaimer.title")}
        </h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          {t("legal.terms.disclaimer.content")}
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">
          {t("legal.terms.law.title")}
        </h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          {t("legal.terms.law.content")}
        </p>
      </section>
    </div>
  );
}

function PrivacyContent() {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col gap-6">
      <p className="text-caption font-caption text-subtext-color">
        {t("legal.privacy.lastUpdated")}
      </p>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">
          {t("legal.privacy.collection.title")}
        </h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          {t("legal.privacy.collection.content")}
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">
          {t("legal.privacy.usage.title")}
        </h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          {t("legal.privacy.usage.content")}
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">
          {t("legal.privacy.sharing.title")}
        </h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          {t("legal.privacy.sharing.content")}
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">
          {t("legal.privacy.storage.title")}
        </h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          {t("legal.privacy.storage.content")}
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">
          {t("legal.privacy.contact.title")}
        </h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          {t("legal.privacy.contact.content")}
        </p>
      </section>
    </div>
  );
}
