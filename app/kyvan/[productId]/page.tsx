"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Image from "next/image";
import {
  ShoppingCart,
  Share2,
  Plus,
  Minus,
  Star,
  Utensils,
  Flame,
  Users,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { getHeatLevelColor, renderStars, salsaProducts } from "../page";
import { useCart } from "@/context/cart-context";
import { toast } from "sonner";

interface TaskPageProps {
  params: Promise<{ productId: string }>;
}

const Product = ({ params }: TaskPageProps) => {
  const [productId, setProductId] = useState<string | null>(null);
  const [product, setProduct] = useState<(typeof salsaProducts)[0] | null>(
    null
  );
  const [selectedSize, setSelectedSize] = useState<string>("8oz");
  const [quantity, setQuantity] = useState<number>(1);
  const [showSizeError, setShowSizeError] = useState(false);
  const router = useRouter();
  const { addToCart } = useCart();

  useEffect(() => {
    const getProductId = async () => {
      const resolvedParams = await params;
      setProductId(resolvedParams.productId);

      // Find the product by ID
      const foundProduct = salsaProducts.find(
        (p) => p.id === parseInt(resolvedParams.productId)
      );
      setProduct(foundProduct || null);
    };
    getProductId();
  }, [params]);

  const handleSizeSelect = (size: string) => {
    setSelectedSize(size);
    setShowSizeError(false);
  };

  const handleQuantityChange = (newQuantity: number) => {
    if (newQuantity >= 1 && newQuantity <= 10) {
      setQuantity(newQuantity);
    }
  };

  const incrementQuantity = () => {
    handleQuantityChange(quantity + 1);
  };

  const decrementQuantity = () => {
    handleQuantityChange(quantity - 1);
  };

  const handleAddToCart = () => {
    if (!selectedSize) {
      setShowSizeError(true);
      return;
    }
    
    if (!product) return;
    
    addToCart({
      id: product.id,
      name: product.name,
      price: product.price,
      image: product.image,
      size: selectedSize,
      quantity: quantity,
      maxQuantity: 10
    });
    
    toast.success("Added to cart!", {
      description: `${quantity}x ${product.name} (${selectedSize}) has been added to your cart.`,
    });
  };

  if (!product) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-white text-xl">Product not found</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Product Details */}
      <section className="bg-gray-50 py-4">
        <div className="px-4">
          <div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 p-8">
              {/* Product Image */}
              <div className="aspect-square bg-gradient-to-br from-neutral-100 to-neutral-50 rounded-lg relative overflow-hidden">
                <Image
                  src={product.image}
                  alt={product.name}
                  fill
                  className="object-contain p-12"
                  sizes="(max-width: 768px) 100vw, 50vw"
                />
              </div>

              {/* Product Details */}
              <div className="space-y-6">
                <div>
                  <h1 className="text-4xl font-bold text-red-600 mb-4">
                    {product.name}
                  </h1>
                  <div className="flex items-center space-x-4 mb-4">
                    <span className="text-2xl font-bold text-neutral-900">
                      ${product.price}
                    </span>
                    {product.originalPrice && (
                      <span className="text-lg text-neutral-500 line-through">
                        ${product.originalPrice}
                      </span>
                    )}
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-neutral-900 mb-3">
                    Select size:
                  </h3>
                  <div className="flex gap-3 mb-2">
                    {product.sizes.map((size) => (
                      <Button
                        key={size}
                        onClick={() => handleSizeSelect(size)}
                        variant={selectedSize === size ? "default" : "outline"}
                        size="lg"
                        className={`flex-col h-auto py-3 px-6 gap-0 transition-all duration-200 ${
                          selectedSize === size
                            ? "bg-red-600 hover:bg-red-700 border-red-600 text-white shadow-md"
                            : "border-red-600 text-red-600 hover:bg-red-50 hover:text-red-700"
                        }`}
                      >
                        <div className="text-lg font-bold leading-tight">
                          {size.replace("oz", "")}
                        </div>
                        <div className="text-xs font-medium leading-tight -mt-1">
                          OZ
                        </div>
                      </Button>
                    ))}
                  </div>
                  {showSizeError && (
                    <p className="text-red-500 text-sm mt-2 animate-pulse">
                      Please select a size before adding to cart
                    </p>
                  )}
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-neutral-900 mb-3">
                    Quantity:
                  </h3>
                  <div className="flex items-center gap-3 mb-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={decrementQuantity}
                      disabled={quantity <= 1}
                      className="w-10 h-10 rounded-full border-red-600 text-red-600 hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Minus className="h-4 w-4" />
                    </Button>
                    <span className="text-lg font-semibold min-w-[3rem] text-center">
                      {quantity}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={incrementQuantity}
                      disabled={quantity >= 10}
                      className="w-10 h-10 rounded-full border-red-600 text-red-600 hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div className="flex gap-4">
                  <Button
                    onClick={handleAddToCart}
                    className="bg-red-600 hover:bg-red-700 text-white px-8 py-3 rounded-full transition-colors"
                  >
                    <ShoppingCart className="h-4 w-4 mr-2" />
                    Add to cart
                  </Button>
                  <Button
                    variant="outline"
                    className="border-neutral-300 text-neutral-700 px-8 py-3 rounded-full"
                  >
                    <Share2 className="h-4 w-4 mr-2" />
                    Share
                  </Button>
                </div>

                <div className="space-y-6">
                  <p className="text-neutral-700 leading-relaxed text-sm">
                    {product.description}
                  </p>

                  {/* Product Information Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-white rounded-lg border border-neutral-200 p-4">
                      <div className="flex items-center gap-3 mb-3">
                        <Utensils className="h-5 w-5 text-red-600" />
                        <span className="font-semibold text-neutral-900">
                          Product Details
                        </span>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-neutral-600">
                            Serving size:
                          </span>
                          <span className="text-sm font-medium text-neutral-900">
                            {product.servingSize}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-neutral-600">
                            Heat level:
                          </span>
                          <Badge
                            variant="outline"
                            className={`${getHeatLevelColor(
                              product.heatLevel
                            )} border`}
                          >
                            <Flame className="h-3 w-3 mr-1" />
                            {product.heatLevel}
                          </Badge>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white rounded-lg border border-neutral-200 p-4">
                      <div className="flex items-center gap-3 mb-3">
                        <Users className="h-5 w-5 text-red-600" />
                        <span className="font-semibold text-neutral-900">
                          Customer Reviews
                        </span>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          {renderStars(product.rating)}
                          <span className="text-sm font-medium text-neutral-900">
                            {product.rating}/5
                          </span>
                        </div>
                        <p className="text-sm text-neutral-600">
                          Based on {product.reviews} reviews
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Selection Summary */}
                  <div className="bg-red-50 rounded-lg border border-red-200 p-4">
                    <h4 className="font-semibold text-red-800 mb-3">
                      Your Selection
                    </h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-red-600">Size:</span>
                        <Badge
                          variant="outline"
                          className="border-red-600 text-red-600"
                        >
                          {selectedSize}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-red-600">Quantity:</span>
                        <Badge
                          variant="outline"
                          className="border-red-600 text-red-600"
                        >
                          {quantity}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Product;
