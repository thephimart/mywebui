interface FeatureUnavailableProps {
  feature?: string;
  message?: string;
}

export function FeatureUnavailable({
  feature = 'This feature',
  message = 'is disabled or not available in this deployment.',
}: FeatureUnavailableProps) {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="text-center">
        <div className="text-muted-foreground mb-2">
          <span className="text-2xl">🚫</span>
        </div>
        <h3 className="font-medium text-lg">{feature}</h3>
        <p className="text-muted-foreground text-sm">{message}</p>
      </div>
    </div>
  );
}
