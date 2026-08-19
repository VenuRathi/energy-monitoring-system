export function toExplicitOffsetDateTime(value: string): string {
  if (!value || value.includes("Z") || /[+-]\d{2}:\d{2}$/.test(value)) {
    return value;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  const offsetMinutes = -parsed.getTimezoneOffset();
  const sign = offsetMinutes >= 0 ? "+" : "-";
  const absoluteOffset = Math.abs(offsetMinutes);
  const hours = String(Math.floor(absoluteOffset / 60)).padStart(2, "0");
  const minutes = String(absoluteOffset % 60).padStart(2, "0");
  return `${value}:00${sign}${hours}:${minutes}`;
}

export function getDeliveryTime(readingTime: string, delayMinutes = 5): string {
  const [hours, minutes] = readingTime.split(":").map(Number);
  if (!Number.isFinite(hours) || !Number.isFinite(minutes)) {
    return "--:--";
  }

  const totalMinutes = (hours * 60 + minutes + delayMinutes) % (24 * 60);
  return `${String(Math.floor(totalMinutes / 60)).padStart(2, "0")}:${String(totalMinutes % 60).padStart(2, "0")}`;
}
