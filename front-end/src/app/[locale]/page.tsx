
import { getHomeData } from "@/services/home";
import Hero from "../Components/Hero/Hero";


export default async function HomePage() {
  try {
    await getHomeData();
  } catch (error) {
    console.error("Failed to fetch homepage data:", error);
  }

  return (
    <main>
      <Hero />
    </main>
  );
}
