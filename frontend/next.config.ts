import type { NextConfig } from "next";

const config: NextConfig = {
  // Keep the repository's existing AGENTS.md as the source of coding standards.
  agentRules: false,
};

export default config;
