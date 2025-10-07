// src/types/account.ts
export interface Account {
  id: string;
  display_name: string;
  username?: string;
  authenticated?: boolean;
  sync_status?: string;
}
