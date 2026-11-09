"use client"

import { useRouter, usePathname } from "@/i18n/navigation";
import { useLocale } from "next-intl";
import { Languages } from "lucide-react";

export default function LanguageSwitcher() {
    const locale = useLocale();
    const pathName = usePathname();
    const router = useRouter();

    const nextLocale = locale === 'en' ? "ar" : 'en';

    function toggleLang() {
        router.replace(pathName, { locale: nextLocale })
    }
    return (
        <button
            onClick={toggleLang}
            className="p-2 rounded-ctl hover:bg-ink-3 transition-colors"
            aria-label="Toggle language"
            title={locale === "en" ? "Switch to Arabic" : "Switch to English"}
        >
            <Languages size={20} />
        </button>
    )
}
