const OPTIMISTIC_PLACEHOLDER_TTL_MS = 30_000;

export function isOptimisticItemExpired(item, now) {
  return now - item.startedAt > OPTIMISTIC_PLACEHOLDER_TTL_MS;
}
