
"use client";

import { Link } from "@/i18n/navigation";
import Image from "next/image";
import { useTranslations } from "next-intl";
import { MapPin, Phone, Clock } from "lucide-react";
import { FaFacebookF, FaInstagram } from "react-icons/fa6";

export default function Footer() {
    const t = useTranslations("Footer");

    return (
        <footer className="bg-ink text-white/70">
            <div className="mx-auto max-w-6xl px-4 py-16">

                {/* Main Footer */}
                <div className="grid grid-cols-1 gap-12 sm:grid-cols-2 lg:grid-cols-4">

                    {/* Brand */}
                    <div className="space-y-5">
                        <Link href="/" aria-label="MOODS home">
                            <Image
                                src="/logo-white.png"
                                alt="MOODS"
                                width={64}
                                height={64}
                                className="h-16 w-16 object-contain"
                            />
                        </Link>

                        <p className="max-w-xs text-sm leading-7">
                            {t("description")}
                        </p>

                        <div className="flex items-center gap-3">
                            <a href="#" aria-label="Facebook" className="rounded-full bg-ink-3 p-2.5 transition hover:bg-flame hover:text-ink">
                                <FaFacebookF size={18} />
                            </a>

                            <a href="#" aria-label="Instagram" className="rounded-full bg-ink-3 p-2.5 transition hover:bg-flame hover:text-ink">
                                <FaInstagram size={18} />
                            </a>
                        </div>
                    </div>

                    {/* Quick Links */}
                    <div>
                        <h3 className="mb-5 text-lg font-bold text-white">
                            {t("quickLinks")}
                        </h3>

                        <ul className="space-y-3 text-sm">
                            <li><Link href="/" className="transition hover:text-flame">{t("home")}</Link></li>
                            <li><Link href="/menu" className="transition hover:text-flame">{t("menu")}</Link></li>
                            <li><Link href="/about" className="transition hover:text-flame">{t("about")}</Link></li>
                            <li><Link href="/contact" className="transition hover:text-flame">{t("contact")}</Link></li>
                        </ul>
                    </div>

                    {/* Contact */}
                    <div>
                        <h3 className="mb-5 text-lg font-bold text-white">
                            {t("contactTitle")}
                        </h3>

                        <ul className="space-y-4 text-sm">
                            <li className="flex items-start gap-3">
                                <MapPin size={18} className="mt-1 shrink-0 text-flame" />
                                <span>{t("address")}</span>
                            </li>

                            <li className="flex items-center gap-3">
                                <Phone size={18} className="shrink-0 text-flame" />
                                <span>{t("phone")}</span>
                            </li>
                        </ul>
                    </div>

                    {/* Opening Hours */}
                    <div>
                        <h3 className="mb-5 text-lg font-bold text-white">
                            {t("openingHours")}
                        </h3>

                        <div className="flex items-start gap-3 text-sm">
                            <Clock size={18} className="mt-1 shrink-0 text-flame" />
                            <p className="leading-7">{t("hours")}</p>
                        </div>
                    </div>

                </div>

                {/* Bottom Bar */}
                <div className="mt-14 flex flex-col items-center justify-between gap-4 border-t border-white/10 pt-6 text-xs sm:flex-row">
                    <p>{t("copyright")}</p>

                    <div className="flex gap-5">
                        <Link href="/privacy" className="transition hover:text-flame">
                            {t("privacy")}
                        </Link>

                        <Link href="/terms" className="transition hover:text-flame">
                            {t("terms")}
                        </Link>
                    </div>
                </div>

            </div>
        </footer>
    );
}
