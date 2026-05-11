"use client";
import { useAuthStore } from "@/store/authStore";
import { useRouter } from "next/navigation";
import { LogOut, User } from "lucide-react";

export default function Topbar() {
  const { user, logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <div />
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <div className="w-7 h-7 bg-teal-100 rounded-full flex items-center justify-center">
            <User size={14} className="text-teal-700" />
          </div>
          <span className="font-medium">{user?.full_name || user?.email}</span>
          <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full capitalize">
            {user?.role}
          </span>
        </div>
        <button
          onClick={handleLogout}
          className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          title="Logout"
        >
          <LogOut size={16} />
        </button>
      </div>
    </header>
  );
}