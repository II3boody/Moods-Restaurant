
import Image from "next/image";
import { Link } from "@/i18n/navigation";
import { useTranslations } from "next-intl";

export default function Hero() {
    const t = useTranslations("Hero");

    return (
        <section className="relative isolate overflow-hidden bg-ink text-white">
            {/* Background Image */}
            <Image
                src="/images/HERO.jpg"
                alt="Moods Restaurant Food"
                fill
                priority
                sizes="100vw"
                className="-z-20 object-cover"
            />

            {/* Dark Overlay */}
            <div className="absolute inset-0 -z-10 bg-black/65" />

            <div className="mx-auto grid min-h-[480px] max-w-6xl grid-cols-1 items-center gap-10 px-4 py-16 md:grid-cols-2">
                {/* Text Content */}
                <div>
                    <p className="mb-3 font-semibold text-flame">
                        MOODS Restaurant & Cafe
                    </p>

                    <h1 className="text-4xl font-extrabold leading-tight sm:text-5xl">
                        {t("title")}
                    </h1>

                    <p className="mt-4 max-w-md leading-7 text-white/80">
                        {t("description")}
                    </p>




                    <div className="mt-8 flex flex-wrap items-center gap-3">
                        <Link
                            href="/menu"
                            className="rounded-md bg-flame px-7 py-3 text-sm font-semibold text-ink transition hover:bg-flame-deep"
                        >
                            {t("orderNow")}
                        </Link>

                        <Link
                            href="/festival"
                            className="rounded-md border border-white/30 px-7 py-3 text-sm font-semibold text-white transition hover:border-white hover:bg-white/10"
                        >
                            {t("offers")}
                        </Link>
                    </div>



                </div>

                {/* Logo */}
                <div className="flex items-center justify-center">
                    <Image
                        src="/logo-white.png"
                        alt="Moods Restaurant & Cafe Logo"
                        width={320}
                        height={320}
                        priority
                        className="h-auto w-52 object-contain sm:w-64 md:w-72"
                    />
                </div>
            </div>
        </section>
    );
}
