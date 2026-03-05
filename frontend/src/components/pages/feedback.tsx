"use client";

import { FeatherCheckCircle } from "@subframe/core";
import { useState } from "react";
import { Accordion } from "@/ui/components/Accordion";
import { Alert } from "@/ui/components/Alert";
import { Button } from "@/ui/components/Button";
import { Select } from "@/ui/components/Select";
import { TextArea } from "@/ui/components/TextArea";
import { TextField } from "@/ui/components/TextField";

const faqItems = [
  {
    question: "AIRASで生成された研究成果の著作権はどうなりますか？",
    answer:
      "AIRASを通じて生成された研究成果の著作権は、原則としてユーザーに帰属します。ただし、AIが生成したコンテンツに関する法的な取り扱いは各国の法律により異なるため、詳細は利用規約をご確認ください。",
  },
  {
    question: "無料プランと有料プランの違いは何ですか？",
    answer:
      "無料プランでは月間の検証回数と利用可能なAIモデルに制限があります。有料プランでは無制限の検証、高性能なAIモデルへのアクセス、優先サポートなどの追加機能をご利用いただけます。",
  },
  {
    question: "データのセキュリティはどのように保護されていますか？",
    answer:
      "すべてのデータは暗号化された通信で転送され、セキュアなクラウドインフラストラクチャに保管されます。定期的なセキュリティ監査を実施し、業界標準のセキュリティプラクティスに従っています。",
  },
];

export function FeedbackPage() {
  const [category, setCategory] = useState("");
  const [subject, setSubject] = useState("");
  const [detail, setDetail] = useState("");
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

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
          お問い合わせ・フィードバック
        </h1>
        <p className="text-caption font-caption text-subtext-color mt-1">
          ご意見・ご要望をお聞かせください
        </p>

        <div className="mt-6 flex gap-8 items-start flex-col lg:flex-row">
          <div className="flex-1 w-full">
            {submitted && (
              <div className="mb-4">
                <Alert
                  variant="success"
                  icon={<FeatherCheckCircle />}
                  title="フィードバックを送信しました。ありがとうございます！"
                  description="内容を確認し、必要に応じてご連絡いたします。"
                />
              </div>
            )}

            <form
              onSubmit={handleSubmit}
              className="rounded-lg border border-border bg-card p-6 flex flex-col gap-5"
            >
              <Select
                label="カテゴリ"
                placeholder="カテゴリを選択"
                value={category}
                onValueChange={setCategory}
              >
                <Select.Item value="バグ報告">バグ報告</Select.Item>
                <Select.Item value="機能リクエスト">機能リクエスト</Select.Item>
                <Select.Item value="一般的な質問">一般的な質問</Select.Item>
                <Select.Item value="その他">その他</Select.Item>
              </Select>

              <TextField label="件名">
                <TextField.Input
                  placeholder="件名を入力してください"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                />
              </TextField>

              <TextArea label="詳細">
                <TextArea.Input
                  placeholder="詳細な内容を入力してください"
                  value={detail}
                  onChange={(e) => setDetail(e.target.value)}
                />
              </TextArea>

              <TextField label="メールアドレス（任意）" helpText="返信が必要な場合はご記入ください">
                <TextField.Input
                  placeholder="example@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </TextField>

              <div className="flex justify-end">
                <Button type="submit">送信</Button>
              </div>
            </form>
          </div>

          <div className="w-full lg:w-80 shrink-0">
            <div className="rounded-lg border border-border bg-card p-6">
              <h2 className="text-body-bold font-body-bold text-default-font mb-4">よくある質問</h2>
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
