export async function requireAuth() {
  const session = { user: { role: "admin" } };
  return session;
}
