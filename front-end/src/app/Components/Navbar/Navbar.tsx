
"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { usePathname } from "@/i18n/navigation";
import { UserRound, ShoppingBag } from "lucide-react";
import LanguageSwitcher from "../LanguageSwitcher/LanguageSwitcher";
import Image from "next/image";

const links = [
    { href: "/", key: "home" },
    { href: "/menu", key: "menu" },
    { href: "/about", key: "about" },
    { href: "/contact", key: "contact" },
] as const;

export default function Navbar() {
    const t = useTranslations("Navbar");
    const pathname = usePathname();

    return (
        <header className="sticky top-0 z-40 bg-ink text-white">
            <div className="mx-auto flex h-16 max-w-6xl items-center gap-4 px-4">
                {/* Logo */}
                <Link href="/" aria-label="MOODS home">
                    <Image
                        src="/logo-white.png"
                        alt="MOODS"
                        width={44}
                        height={44}
                        priority
                        className="h-11 w-11 object-contain"
                    />
                </Link>

                {/* Desktop Navigation */}
                <nav aria-label="Main" className="hidden flex-1 gap-1 md:flex">
                    {links.map(({ href, key }) => {
                        const isActive =
                            pathname === href ||
                            (href !== "/" && pathname.startsWith(`${href}/`));

                        return (
                            <Link
                                key={href}
                                href={href}
                                className={`rounded-ctl px-3 py-2 text-sm font-medium transition-colors ${isActive
                                    ? "text-flame"
                                    : "text-white/80 hover:text-white"
                                    }`}
                            >
                                {t(key)}
                            </Link>
                        );
                    })}
                </nav>

                <div className="flex-1 md:hidden" />

                {/* Actions */}
                <div className="flex items-center gap-1">
                    <LanguageSwitcher />

                    <Link
                        href="/login"
                        className="rounded-ctl p-2 transition-colors hover:bg-ink-3"
                        aria-label="Account"
                    >
                        <UserRound size={20} />
                    </Link>

                    <Link
                        href="/cart"
                        className="relative rounded-ctl p-2 transition-colors hover:bg-ink-3"
                        aria-label="Cart"
                    >
                        <ShoppingBag size={20} />
                    </Link>
                </div>
            </div>

            {/* Mobile Navigation */}
            <nav
                aria-label="Mobile"
                className="flex gap-1 overflow-x-auto px-3 pb-2 md:hidden"
            >
                {links.map(({ href, key }) => {
                    const isActive =
                        pathname === href ||
                        (href !== "/" && pathname.startsWith(`${href}/`));

                    return (
                        <Link
                            key={href}
                            href={href}
                            className={`whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-medium ${isActive
                                ? "bg-flame text-ink"
                                : "text-white/80"
                                }`}
                        >
                            {t(key)}
                        </Link>
                    );
                })}
            </nav>
        </header>
    );
}
