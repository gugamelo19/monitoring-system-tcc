export type Asset = {
  id: string;
  name: string;
  hostname?: string | null;
  ip_address: string;
  mac_address?: string | null;
  asset_type: string;
  location?: string | null;
  operating_system?: string | null;
  status: string;
  is_monitored: boolean;
  created_at: string;
  updated_at: string;
};
