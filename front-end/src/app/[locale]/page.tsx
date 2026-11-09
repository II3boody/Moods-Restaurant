
import { useTranslations } from "next-intl";
import LanguageSwitcher from "../Components/LanguageSwitcher/LanguageSwitcher";

export default function HomePage() {
  const t = useTranslations("HomePage");

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4">
      <h1 className="text-3xl font-bold">{t("title")}</h1>
      <p>{t("description")}</p>
      <LanguageSwitcher />
    </main>
  );
}
