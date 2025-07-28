interface EmptyStateProps {
  heading: string;
  subheading: string;
}

export default function EmptyState({ heading, subheading }: EmptyStateProps) {
  return (
    <div className="flex-none w-full h-48 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center">
      <div className="text-center">
        <p className="text-muted-foreground mb-2">{heading}</p>
        <p className="text-xs text-muted-foreground">{subheading}</p>
      </div>
    </div>
  );
}
