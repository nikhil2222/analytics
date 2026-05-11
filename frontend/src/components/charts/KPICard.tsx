interface KPICardProps {
  title: string;
  value: number | string;
  label?: string;
}

export default function KPICard({ title, value, label }: KPICardProps) {
  return (
    <div className="flex flex-col justify-between h-full">
      <p className="text-sm font-medium text-gray-500">{title}</p>
      <div>
        <p className="text-4xl font-bold text-gray-900 mt-2">
          {typeof value === "number" ? value.toLocaleString() : value}
        </p>
        {label && <p className="text-sm text-gray-400 mt-1">{label}</p>}
      </div>
    </div>
  );
}