import { Skeleton } from "../ui/skeleton";
import { Waypoints } from "lucide-react";

export default function LoadingToolsSkeleton() {
  return (
    <div className="h-full bg-gray-50 border-r border-gray-200 flex flex-col">
      <div className="flex items-center gap-2 p-4 border-b border-gray-200 flex-shrink-0">
        <Waypoints />
        <h2 className="text-lg font-semibold text-gray-800">Waypoint</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Skeleton categories */}
        {[1, 2, 3].map((categoryIndex) => (
          <div key={categoryIndex} className="space-y-2">
            {/* Category title skeleton */}
            <Skeleton className="h-4 w-20 mb-2" />

            {/* Tool items skeletons */}
            <div className="space-y-2">
              {[1, 2, 3].map((toolIndex) => (
                <div
                  key={toolIndex}
                  className="flex p-3 bg-white rounded-lg border border-gray-200 min-h-[70px]"
                >
                  {/* Icon skeleton */}
                  <div className="mr-3 mt-1">
                    <Skeleton className="w-5 h-5 rounded" />
                  </div>

                  {/* Content skeleton */}
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-full" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
