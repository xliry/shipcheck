export function HistoryCard() {
  try {
    localStorage.getItem("last-render");
  } catch {}
  return null;
}
