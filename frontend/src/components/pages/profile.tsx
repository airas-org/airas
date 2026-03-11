import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Avatar, Badge, Button, TextArea, TextField } from "@/ui";

export function ProfilePage() {
  const { t } = useTranslation();
  const [name, setName] = useState("田中 太郎");
  const [email, setEmail] = useState("tanaka@example.com");
  const [affiliation, setAffiliation] = useState("東京大学 情報理工学系研究科");
  const [bio, setBio] = useState(
    "機械学習と自然言語処理を専門とする研究者。特にLLMの推論能力と科学的発見への応用に関心があります。",
  );
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-2xl mx-auto px-8 py-8">
        <h1 className="text-heading-2 font-heading-2 text-default-font mb-8">
          {t("profile.title")}
        </h1>

        <div className="rounded-lg border border-border bg-card p-6 mb-6">
          <div className="flex items-center gap-5 mb-6">
            <Avatar size="x-large" variant="brand">
              田中
            </Avatar>
            <div className="flex flex-col gap-1">
              <span className="text-heading-3 font-heading-3 text-default-font">田中 太郎</span>
              <span className="text-body font-body text-subtext-color">tanaka@example.com</span>
              <Badge variant="brand">{t("profile.researcher")}</Badge>
            </div>
          </div>

          <div className="flex flex-col gap-4">
            <TextField label={t("profile.displayName")}>
              <TextField.Input
                placeholder={t("profile.displayNamePlaceholder")}
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </TextField>
            <TextField label={t("profile.email")}>
              <TextField.Input
                placeholder={t("profile.emailPlaceholder")}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </TextField>
            <TextField label={t("profile.affiliation")}>
              <TextField.Input
                placeholder={t("profile.affiliationPlaceholder")}
                value={affiliation}
                onChange={(e) => setAffiliation(e.target.value)}
              />
            </TextField>
            <TextArea label={t("profile.bio")}>
              <TextArea.Input
                placeholder={t("profile.bioPlaceholder")}
                value={bio}
                onChange={(e) => setBio(e.target.value)}
              />
            </TextArea>

            <div className="flex items-center gap-3 pt-2">
              <Button onClick={handleSave}>{t("profile.save")}</Button>
              {saved && (
                <span className="text-caption font-caption text-success-800">
                  {t("profile.saved")}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
