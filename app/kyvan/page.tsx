"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Image from "next/image";
import { Star, Flame, ShoppingCart } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCart } from "@/context/cart-context";
import { toast } from "sonner";

export const salsaProducts = [
  {
    id: 1,
    name: "Sweet Potato BBQ Sauce",
    brand: "Kyvan",
    description:
      "Rich and smoky BBQ sauce featuring roasted sweet potatoes for natural sweetness and depth. This unique blend combines traditional BBQ flavors with the earthy sweetness of sweet potato, creating a perfect balance for grilled meats and vegetables.",
    price: 8.99,
    originalPrice: 10.99,
    image: "/kyvan/spbbq.png",
    heatLevel: "Mild",
    sizes: ["8oz", "16oz", "24oz"],
    selectedSize: "16oz",
    rating: 4.8,
    reviews: 124,
    featured: true,
    servingSize: "2 Tbsp (30g)",
  },
  {
    id: 2,
    name: "Honey Apple BBQ Sauce",
    brand: "Kyvan",
    description:
      "Sweet and tangy BBQ sauce infused with pure honey and crisp apple flavors. This delightful combination brings together the natural sweetness of honey with the fresh tartness of apples, creating a perfectly balanced sauce that's ideal for pork, chicken, and ribs.",
    price: 10.99,
    image: "/kyvan/habbq.png",
    heatLevel: "Medium",
    sizes: ["8oz", "12oz", "16oz"],
    selectedSize: "12oz",
    rating: 4.9,
    reviews: 89,
    featured: true,
    servingSize: "2 Tbsp (30g)",
  },
  {
    id: 3,
    name: "Cherry Apple BBQ Sauce",
    brand: "Kyvan",
    description:
      "Bold and fruity BBQ sauce featuring tart cherries and sweet apples in perfect harmony. This gourmet blend offers a sophisticated flavor profile with rich cherry notes and crisp apple undertones, making it exceptional for beef, pork, and grilled vegetables.",
    price: 9.49,
    image: "/kyvan/cabbq.png",
    heatLevel: "Hot",
    sizes: ["8oz", "12oz", "16oz"],
    selectedSize: "16oz",
    rating: 4.7,
    reviews: 67,
    servingSize: "2 Tbsp (30g)",
  },
];

export const renderStars = (rating: number) => {
  const fullStars = Math.floor(rating);
  const partialStar = rating - fullStars;

  return (
    <div className="flex items-center gap-1">
      {[...Array(5)].map((_, index) => {
        if (index < fullStars) {
          // Full star
          return (
            <Star
              key={index}
              className="h-3 w-3 text-yellow-400 fill-yellow-400"
            />
          );
        } else if (index === fullStars && partialStar > 0) {
          // Partial star
          return (
            <div key={index} className="relative h-3 w-3">
              <Star className="h-3 w-3 text-gray-300 absolute" />
              <div
                className="overflow-hidden absolute"
                style={{ width: `${partialStar * 100}%` }}
              >
                <Star className="h-3 w-3 text-yellow-400 fill-yellow-400" />
              </div>
            </div>
          );
        } else {
          // Empty star
          return <Star key={index} className="h-3 w-3 text-gray-300" />;
        }
      })}
    </div>
  );
};

export const getHeatLevelColor = (heatLevel: string) => {
  switch (heatLevel.toLowerCase()) {
    case "mild":
      return "bg-green-100 text-green-800 border-green-200";
    case "medium":
      return "bg-yellow-100 text-yellow-800 border-yellow-200";
    case "hot":
      return "bg-red-100 text-red-800 border-red-200";
    default:
      return "bg-gray-100 text-gray-800 border-gray-200";
  }
};

export default function SalsaShop() {
  const router = useRouter();
  return (
    <div className="min-h-screen">
      {/* Products Grid */}
      <section className="bg-white">
        <div className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {salsaProducts.map((product) => (
              <Card
                key={product.id}
                className="group overflow-hidden hover:shadow-lg transition-all duration-300 border border-neutral-200 bg-white py-0 cursor-pointer"
                onClick={() => router.push(`/veda/${product.id}`)}
              >
                <CardHeader className="p-0 relative">
                  <div className="aspect-square bg-gradient-to-br from-neutral-100 to-neutral-50 relative overflow-hidden">
                    <Image
                      src={product.image}
                      alt={product.name}
                      fill
                      className="object-contain p-8 group-hover:scale-115 transition-transform duration-300"
                      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                    />
                  </div>
                </CardHeader>

                <CardContent className="p-6">
                  <div className="space-y-4">
                    <div className="text-center">
                      <h3 className="font-bold text-lg text-neutral-900 leading-tight mb-2">
                        {product.name}
                      </h3>
                      <div className="flex items-center justify-center gap-2 mb-2">
                        <span className="text-xl font-bold text-neutral-900">
                          ${product.price}
                        </span>
                        {product.originalPrice && (
                          <span className="text-sm text-neutral-500 line-through">
                            ${product.originalPrice}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center justify-center gap-2">
                      {renderStars(product.rating)}
                      <span className="text-xs text-neutral-600">
                        ({product.reviews})
                      </span>
                    </div>

                    <div className="flex justify-center">
                      <Badge
                        variant="outline"
                        className={`${getHeatLevelColor(
                          product.heatLevel
                        )} border text-xs`}
                      >
                        <Flame className="h-3 w-3 mr-1" />
                        {product.heatLevel}
                      </Badge>
                    </div>

                    <div className="space-y-3">
                      <p className="text-xs text-neutral-500 text-center">
                        Available in {product.sizes.length} size
                        {product.sizes.length > 1 ? "s" : ""}:{" "}
                        {product.sizes.join(", ")}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
