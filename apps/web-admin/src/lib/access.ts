export function hasPermission(permissions: string[], permission: string): boolean {
  return permissions.includes("*:*:*") || permissions.includes(permission);
}

export function canReadByDataScope(userDataScope?: string, recordOwnerId?: string, currentUserId?: string) {
  if (!userDataScope || userDataScope === "all") return true;
  if (userDataScope === "self") return Boolean(recordOwnerId && currentUserId && recordOwnerId === currentUserId);
  return false;
}
