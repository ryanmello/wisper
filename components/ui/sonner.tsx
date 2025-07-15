"use client";

import { useTheme } from "next-themes";
import { Toaster as Sonner, ToasterProps } from "sonner";

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme();

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      position="bottom-left"
      expand={false}
      richColors={false}
      closeButton={true}
      toastOptions={{
        classNames: {
          toast:
            "!bg-white !text-gray-900 !border-red-600 !border-2 shadow-xl !rounded-3xl !px-4 !py-3 !font-medium !text-sm !min-w-[280px] !backdrop-blur-sm",
          description: "!text-gray-600 !text-xs !font-normal !mt-0.5 !leading-snug",
          actionButton:
            "!bg-red-600 !text-white hover:!bg-red-700 !rounded-full !px-3 !py-1.5 !text-xs !font-semibold !ml-2 !transition-colors",
          cancelButton:
            "!bg-gray-100 !text-gray-600 !rounded-full !px-3 !py-1.5 !text-xs !font-semibold !ml-2 !transition-colors hover:!bg-gray-200",
          closeButton:
            "!bg-gray-100 hover:!bg-gray-200 !text-gray-600 !rounded-full !transition-colors !w-5 !h-5 !p-1",
          title: "!text-gray-900 !font-semibold !text-sm !leading-tight",
          icon: "!text-red-600 !w-4 !h-4",
        },
        duration: 2000,
      }}
      {...props}
    />
  );
};

export { Toaster };
