import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
};

export const getRepoName = (repo: string) => {
  if (repo.includes("github.com")) {
    const match = repo.match(/github\.com\/([^\/]+\/[^\/]+)/);
    return match ? match[1] : repo;
  }
  return repo;
};