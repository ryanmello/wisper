"use client";

import Image from "next/image";
import {
  X,
  Plus,
  Minus,
  Trash2,
  ShoppingCart,
  CreditCard,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCart } from "@/context/cart-context";

interface CartSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function CartSidebar({ isOpen, onClose }: CartSidebarProps) {
  const { items, updateQuantity, removeFromCart, getTotalPrice } = useCart();

  const formatPrice = (price: number) => {
    return `$${price.toFixed(2)}`;
  };

  const handleQuantityChange = (
    id: number,
    size: string,
    newQuantity: number
  ) => {
    if (newQuantity <= 0) {
      removeFromCart(id, size);
    } else {
      updateQuantity(id, size, newQuantity);
    }
  };

  return (
    <>
      {/* Sidebar */}
      <div
        className={`fixed top-0 right-0 h-full w-96 bg-white shadow-2xl transform transition-transform duration-300 ease-in-out z-50 border-l border-neutral-300 ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-2 border-b border-neutral-100">
            <div>
              <h2 className="text-xl font-bold text-neutral-900">Cart</h2>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="hover:bg-white hover:shadow-md rounded-full transition-all duration-200 border border-transparent hover:border-neutral-200"
            >
              <X className="h-5 w-5 text-neutral-600" />
            </Button>
          </div>

          {/* Cart Items */}
          <div className="flex-1 overflow-y-auto p-6 bg-gradient-to-b from-neutral-50/30 to-white">
            {items.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full px-8 py-12">
                <div className="relative mb-8">
                  {/* Animated background circles */}
                  <div className="absolute inset-0 rounded-full bg-gradient-to-br from-red-100 via-red-50 to-orange-50 w-32 h-32 animate-pulse"></div>
                  <div
                    className="absolute inset-2 rounded-full bg-gradient-to-br from-red-50 to-white w-28 h-28 animate-pulse"
                    style={{ animationDelay: "0.5s" }}
                  ></div>

                  {/* Main icon container */}
                  <div className="relative flex items-center justify-center w-32 h-32 bg-gradient-to-br from-red-500 to-red-600 rounded-full shadow-2xl">
                    <ShoppingCart className="h-16 w-16 text-white" />
                  </div>

                  {/* Floating accent */}
                  <div className="absolute -top-2 -right-2 w-6 h-6 bg-yellow-400 rounded-full shadow-lg animate-bounce"></div>
                </div>

                <div className="text-center space-y-4 max-w-sm">
                  <h3 className="text-xl font-semibold text-neutral-900 mb-2">
                    Your cart awaits
                  </h3>
                  <p className="text-neutral-600 text-sm">
                    Add some flavors to get started on your culinary journey.
                  </p>

                  <div className="pt-4">
                    <Button
                      onClick={onClose}
                      className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
                    >
                      <ShoppingCart className="h-4 w-4 mr-2" />
                      Start Shopping
                    </Button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {items.map((item) => (
                  <div
                    key={`${item.id}-${item.size}`}
                    className="bg-white border border-neutral-200 rounded-2xl p-4 shadow-sm hover:shadow-md transition-all duration-200 hover:border-red-200"
                  >
                    <div className="flex items-center gap-4">
                      <div className="relative w-16 h-16 bg-gradient-to-br from-neutral-100 to-neutral-50 rounded-xl overflow-hidden shadow-sm">
                        <Image
                          src={item.image}
                          alt={item.name}
                          fill
                          className="object-contain p-2"
                        />
                      </div>

                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-neutral-900 text-sm truncate">
                          {item.name}
                        </h3>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-neutral-500">
                            Size:
                          </span>
                          <span className="text-xs font-medium text-neutral-700 bg-neutral-100 px-2 py-0.5 rounded-full">
                            {item.size}
                          </span>
                        </div>
                        <p className="text-red-600 font-bold text-sm mt-1">
                          {formatPrice(item.price)}
                        </p>
                      </div>

                      <div className="flex flex-col items-end gap-2">
                        <div className="flex items-center gap-1 bg-neutral-100 rounded-full p-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              handleQuantityChange(
                                item.id,
                                item.size,
                                item.quantity - 1
                              )
                            }
                            className="w-6 h-6 p-0 hover:bg-red-100 hover:text-red-600 rounded-full transition-colors"
                            disabled={item.quantity <= 1}
                          >
                            <Minus className="h-3 w-3" />
                          </Button>
                          <span className="w-8 text-center text-sm font-semibold text-neutral-900">
                            {item.quantity}
                          </span>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              handleQuantityChange(
                                item.id,
                                item.size,
                                item.quantity + 1
                              )
                            }
                            className="w-6 h-6 p-0 hover:bg-red-100 hover:text-red-600 rounded-full transition-colors"
                            disabled={item.quantity >= (item.maxQuantity || 10)}
                          >
                            <Plus className="h-3 w-3" />
                          </Button>
                        </div>

                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeFromCart(item.id, item.size)}
                          className="w-8 h-8 p-0 text-neutral-400 hover:text-red-600 hover:bg-red-50 rounded-full transition-all duration-200"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          {items.length > 0 && (
            <div className="border-t border-neutral-100 bg-gradient-to-t from-neutral-50/50 to-white p-6 space-y-4">
              <div className="bg-white rounded-2xl p-4 shadow-sm border border-neutral-200">
                <div className="flex justify-between items-center">
                  <span className="text-lg font-semibold text-neutral-900">
                    Total:
                  </span>
                  <span className="text-lg font-bold text-red-600">
                    {formatPrice(getTotalPrice())}
                  </span>
                </div>
                <p className="text-xs text-neutral-500 mt-1">
                  Shipping calculated at checkout
                </p>
              </div>

              <div className="space-y-3">
                <Button
                  className="w-full bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white shadow-lg hover:shadow-xl transition-all duration-200 rounded-xl font-semibold"
                  size="lg"
                >
                  <CreditCard className="h-4 w-4 mr-2" />
                  Proceed to Checkout
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
