"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { useAuth } from "@/context/auth-context";
import {
  Fingerprint,
  LogOut,
  Settings,
  HelpCircle,
  Waypoints,
  Sparkles,
  Flower,
  Layers,
} from "lucide-react";

export default function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [showUserTooltip, setShowUserTooltip] = useState(false);
  const userTooltipRef = useRef<HTMLDivElement>(null);
  const userAvatarRef = useRef<HTMLButtonElement>(null);

  // Close tooltip when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        userTooltipRef.current &&
        !userTooltipRef.current.contains(event.target as Node) &&
        userAvatarRef.current &&
        !userAvatarRef.current.contains(event.target as Node)
      ) {
        setShowUserTooltip(false);
      }
    };

    if (showUserTooltip) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showUserTooltip]);

  const handleDisconnect = () => {
    setShowUserTooltip(false);
    logout();
  };

  const handleNavigation = (path: string) => {
    router.push(path);
  };

  const isActivePage = (path: string) => {
    if (path === "/") return pathname === "/";
    return pathname.startsWith(path);
  };

  const mainNavItems = [
    { icon: Sparkles, path: "/", title: "Conscience" },
    { icon: Fingerprint, path: "/cipher", title: "Cipher" },
    { icon: Flower, path: "/veda", title: "Veda" },
    { icon: Waypoints, path: "/waypoint", title: "Waypoint" },
    { icon: Layers, path: "/playbook", title: "Playbook" },
  ];

  const helpNavItems = [{ icon: HelpCircle, path: "/docs", title: "Help" }];

  return (
    <div className="w-16 bg-card/80 backdrop-blur-sm border-r border-border flex flex-col fixed left-0 top-0 h-full z-40">
      <nav className="flex-1 p-2 space-y-2">
        <div className="h-full flex flex-col justify-between">
          <div className="space-y-2">
            {mainNavItems.map(({ icon: Icon, path, title }) => (
              <Button
                key={path}
                variant="ghost"
                size="icon"
                onClick={() => handleNavigation(path)}
                title={title}
                className={cn(
                  "w-full h-10 rounded-lg",
                  isActivePage(path)
                    ? "bg-primary/10 text-primary hover:bg-primary/15"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Icon size={18} />
              </Button>
            ))}
          </div>

          {helpNavItems.map(({ icon: Icon, path, title }) => (
            <Button
              key={path}
              variant="ghost"
              size="icon"
              onClick={() => handleNavigation(path)}
              title={title}
              className={cn(
                "w-full h-10 rounded-lg",
                isActivePage(path)
                  ? "bg-primary/10 text-primary hover:bg-primary/15"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Icon size={18} />
            </Button>
          ))}
        </div>
      </nav>

      {/* Sidebar Footer - User Profile */}
      {user && (
        <div className="p-3 border-t border-border relative">
          <Button
            ref={userAvatarRef}
            variant="ghost"
            size="icon"
            onClick={() => setShowUserTooltip(!showUserTooltip)}
            className="w-full h-auto p-0 group hover:bg-transparent"
          >
            <Avatar
              className={cn(
                "w-8 h-8 cursor-pointer transition-all duration-200",
                "group-hover:scale-105 group-hover:shadow-lg",
                showUserTooltip
                  ? "ring-2 ring-primary/60 shadow-lg scale-105"
                  : "group-hover:ring-2 group-hover:ring-primary/30"
              )}
            >
              <AvatarImage
                src={user.avatar_url}
                alt={user.login}
                className="object-cover"
              />
              <AvatarFallback className="bg-primary/10 text-primary font-semibold">
                {user.login.charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>
          </Button>

          {/* User Tooltip */}
          {showUserTooltip && (
            <div
              ref={userTooltipRef}
              className="absolute bottom-full left-2 mb-3 bg-card/95 backdrop-blur-sm border border-border rounded-xl shadow-xl p-4 min-w-[240px] z-50 animate-in fade-in-0 slide-in-from-bottom-2 duration-200"
            >
              {/* Header */}
              <div className="flex items-center gap-3 mb-4">
                <Avatar className="w-10 h-10 ring-2 ring-border">
                  <AvatarImage
                    src={user.avatar_url}
                    alt={user.login}
                    className="object-cover"
                  />
                  <AvatarFallback className="bg-primary/10 text-primary font-semibold text-sm">
                    {user.login.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-foreground truncate">
                    {user.name || user.login}
                  </p>
                  <p className="text-xs text-muted-foreground truncate font-medium">
                    @{user.login}
                  </p>
                </div>
              </div>

              {/* Menu Options */}
              <div className="space-y-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setShowUserTooltip(false);
                    handleNavigation("/settings");
                  }}
                  className="w-full justify-start hover:bg-muted/80 transition-all duration-200 font-medium"
                >
                  <Settings size={14} className="mr-2" />
                  Settings
                </Button>

                <div className="border-t border-border my-2"></div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDisconnect}
                  className="w-full hover:bg-destructive/10 hover:text-destructive hover:border-destructive/30 transition-all duration-200 font-medium"
                >
                  <LogOut size={14} className="mr-2" />
                  Disconnect Account
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
