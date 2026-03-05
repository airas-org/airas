"use client";

import { useState } from "react";

type Tab = "terms" | "privacy";

export function LegalPage() {
  const [activeTab, setActiveTab] = useState<Tab>("terms");

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-8 py-8">
        <h1 className="text-heading-2 font-heading-2 text-default-font">法的情報</h1>
        <p className="text-caption font-caption text-subtext-color mt-1">
          サービスのご利用に関する規約とポリシー
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
            利用規約
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
            プライバシーポリシー
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
  return (
    <div className="flex flex-col gap-6">
      <p className="text-caption font-caption text-subtext-color">最終更新日: 2026年3月1日</p>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">サービスの概要</h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          AIRASは、AIを活用した研究支援プラットフォームです。本サービスは、仮説の生成、検証計画の立案、実験コードの自動生成、および論文執筆の支援を提供します。本規約は、サービスのご利用に際して適用される条件を定めるものです。
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">利用条件</h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          本サービスをご利用いただくには、18歳以上であること、または法定代理人の同意を得ていることが必要です。ユーザーは、本サービスを学術研究および正当な目的にのみ使用するものとします。不正な利用が確認された場合、アカウントを停止する場合があります。
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">アカウント</h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          ユーザーは、正確かつ最新の情報を提供してアカウントを作成する必要があります。アカウントの認証情報は厳重に管理し、第三者と共有しないでください。アカウントにおけるすべての活動について、ユーザーが責任を負うものとします。
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">知的財産権</h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          本サービスを通じて生成されたコンテンツの知的財産権は、適用される法律に従って取り扱われます。ユーザーが入力したデータおよび研究成果に関する権利は、原則としてユーザーに帰属します。ただし、サービスの改善のために匿名化されたデータを利用する場合があります。
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">免責事項</h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          本サービスは「現状有姿」で提供され、AIが生成する結果の正確性を保証するものではありません。研究成果の最終的な検証はユーザーの責任において行ってください。サービスの中断または停止により生じた損害について、当社は責任を負いかねます。
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">準拠法</h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          本規約は日本法に準拠し、解釈されるものとします。本規約に関連する紛争については、東京地方裁判所を第一審の専属的合意管轄裁判所とします。
        </p>
      </section>
    </div>
  );
}

function PrivacyContent() {
  return (
    <div className="flex flex-col gap-6">
      <p className="text-caption font-caption text-subtext-color">最終更新日: 2026年3月1日</p>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">収集する情報</h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          当社は、アカウント作成時にお名前、メールアドレス、所属機関などの情報を収集します。また、サービスの利用状況に関するログデータ（アクセス日時、使用機能、エラー情報等）を自動的に収集します。研究データについては、ユーザーが明示的にアップロードしたもののみを取り扱います。
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">情報の利用目的</h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          収集した情報は、サービスの提供・運営・改善、ユーザーサポートの提供、およびセキュリティの維持のために利用します。匿名化されたデータは、AIモデルの精度向上および研究目的に使用する場合があります。ユーザーの同意なくマーケティング目的で個人情報を使用することはありません。
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">情報の共有</h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          当社は、法律上の義務がある場合を除き、ユーザーの個人情報を第三者と共有することはありません。サービスの提供に必要な範囲で、信頼できるパートナー企業にデータ処理を委託する場合があります。その際、適切な契約およびセキュリティ対策を講じます。
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">データの保管</h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          ユーザーのデータは、適切なセキュリティ対策が施されたサーバーに保管されます。データの保管期間は、アカウントが有効な間およびその後の法律で定められた期間とします。アカウントの削除を要請された場合、合理的な期間内にデータを削除します。
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="text-body-bold font-body-bold text-default-font">お問い合わせ</h3>
        <p className="text-body font-body text-subtext-color leading-relaxed">
          プライバシーポリシーに関するご質問やご要望は、サポートページのお問い合わせフォームよりご連絡ください。データの開示、訂正、削除等のご要請にも対応いたします。
        </p>
      </section>
    </div>
  );
}
