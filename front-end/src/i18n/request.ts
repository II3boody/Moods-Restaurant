
import { getRequestConfig } from "next-intl/server";
import { hasLocale } from "next-intl";
import { routing } from "./routing";

export default getRequestConfig(async ({ requestLocale }) => {
    const requestedLocale = await requestLocale;

    const locale = hasLocale(routing.locales, requestedLocale)
        ? requestedLocale
        : routing.defaultLocale;

    const messages = {
        en: (await import("../../messages/en.json")).default,
        ar: (await import("../../messages/ar.json")).default,
    };

    return {
        locale,
        messages: messages[locale],
    };
});
