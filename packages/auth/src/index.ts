export type UserProfile = {
  id: string;
  username: string;
  full_name?: string;
  roles: string[];
  permissions: string[];
  data_scope?: string;
};
