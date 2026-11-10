
import api from "@/lib/axios";
import type { HomeData } from "@/types/home";

export async function getHomeData(): Promise<HomeData> {
    const response = await api.get<HomeData>("/home");

    return response.data;
}
