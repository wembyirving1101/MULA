import type { Metadata } from "next";
import { TeamPage } from "@/features/team";

export const metadata: Metadata = { title: "Mula · My team" };

export default function Page() {
  return <TeamPage />;
}
