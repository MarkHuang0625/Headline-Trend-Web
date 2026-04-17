export function formatRelativeTime(input: string): string {
  const date = new Date(input);
  const diffMinutes = Math.round((Date.now() - date.getTime()) / 60000);
  if (diffMinutes < 1) return "now";
  if (diffMinutes < 60) return `${diffMinutes}m`;
  const hours = Math.floor(diffMinutes / 60);
  const minutes = diffMinutes % 60;
  return `${hours}h ${minutes}m`;
}

export function formatCategory(value: string): string {
  return value.replace("_", " ").replace(/\b\w/g, (match) => match.toUpperCase());
}

