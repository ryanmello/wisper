"use client";

import { useState } from "react";
import Image from "next/image";
import { Search, ShoppingCart } from "lucide-react";
import { Input } from "@/components/ui/input";
import { usePathname } from "next/navigation";
import { useCart } from "@/context/cart-context";
import CartSidebar from "./CartSidebar";
import Link from "next/link";

export default function Navbar() {
  const pathname = usePathname();
  const { getTotalItems } = useCart();
  const totalItems = getTotalItems();
  const [isCartOpen, setIsCartOpen] = useState(false);

  const isActive = (path: string) => {
    if (path === "/veda") {
      return pathname === "/veda" || pathname.startsWith("/veda/");
    }
    return pathname === path;
  };

  const getLinkClassName = (path: string) => {
    const baseClasses = "transition-colors font-medium";
    const activeClasses = "text-red-600 border-b-2 border-red-600 pb-1";
    const inactiveClasses = "text-neutral-700 hover:text-red-700";
    
    return `${baseClasses} ${isActive(path) ? activeClasses : inactiveClasses}`;
  };

  return (
    <>
      <nav className="bg-white shadow-sm border-b sticky top-0 z-50">
        <div className="px-4 h-20">
          <div className="grid grid-cols-3 items-center h-full">
            {/* Left Section - Logo */}
            <div className="flex items-center space-x-4">
              <Link href="/veda">
                <Image
                  src="/kyvan/kyvan-crop.png"
                  alt="Kyvan"
                  width={120}
                  height={48}
                  className="h-16 w-auto cursor-pointer"
                />
              </Link>
            </div>

            {/* Center Section - Navigation Links */}
            <div className="hidden lg:flex items-center justify-center space-x-6">
              <Link
                href="/veda"
                className={getLinkClassName("/veda")}
              >
                Products
              </Link>
              <Link
                href="/veda/recipes"
                className={getLinkClassName("/veda/recipes")}
              >
                Recipes
              </Link>
              <Link
                href="/veda/contact"
                className={getLinkClassName("/veda/contact")}
              >
                Contact
              </Link>
            </div>

            {/* Right Section - Search and Cart */}
            <div className="flex gap-4 justify-end items-center">
              <div className="hidden md:flex flex-1 max-w-md">
                <div className="relative w-full">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-neutral-400" />
                  <Input
                    placeholder="Search"
                    className="w-full h-10 pl-10 pr-4 border-1 rounded-full border-red-600"
                  />
                </div>
              </div>
              <div 
                className="relative flex items-center space-x-2 border-1 border-red-600 hover:bg-red-50 rounded-full px-4 h-10 cursor-pointer transition-colors duration-300"
                onClick={() => setIsCartOpen(true)}
              >
                <ShoppingCart className="h-4 w-4 text-red-600" />
                <span className="text-red-600 font-medium text-sm">Cart</span>
                {totalItems > 0 && (
                  <div className="absolute -top-2 -right-2 bg-red-600 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">
                    {totalItems > 99 ? "99+" : totalItems}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Cart Sidebar */}
      <CartSidebar 
        isOpen={isCartOpen} 
        onClose={() => setIsCartOpen(false)} 
      />
    </>
  );
}
