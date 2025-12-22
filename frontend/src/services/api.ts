import axios, { AxiosInstance } from 'axios';

const baseURL = import.meta.env.DEV ? '/' : (import.meta.env.VITE_BACKEND_URL || '/');

export const axiosInstance: AxiosInstance = axios.create({
  baseURL,
  withCredentials: true,
});

// Types based on OpenAPI spec
export interface CSVUploadResponse {
  message: string;
  processed_archetypes: number;
  processed_element_types: number;
  processed_components: number;
  processed_products: number;
  processed_component_products: number;
  processed_archetype_elements: number;
  processed_element_components: number;
}

export interface ArchetypeList {
  archetypes: string[];
}

export interface MaterialByElementType {
  product_id: string;
  product_designation: string;
  element_type: string;
  volume: number;
  weight: number;
}

export interface MaterialByProductCategory {
  product_id: string;
  product_designation: string;
  category: string;
  total_volume: number;
  total_weight: number;
}

export interface MaterialEstimationRequest {
  archetype_id: string;
  target_grundflaeche: number;
  target_gebaeudeumrisse: number;
  target_gebaeudehoehe: number;
  refurbishment_level?: string;
}

export interface RefurbishmentOptionsResponse {
  archetype_id: string;
  refurbishment_required: boolean;
  available_levels: string[];
  default_level?: string;
  explanation?: string;
}

export interface MaterialEstimationResponse {
  by_element_type: MaterialByElementType[];
  by_product_category: MaterialByProductCategory[];
  calculation_factors: Record<string, any>;
  window_data: [string, string, number][];
}

export interface BuildingEstimationRequest {
  address: string;
}

export interface BuildingEstimationResponse {
  grundflaeche: number;
  gebaeudeumfang: number;
  gebaeudehoehe: number | null;
  height_available: boolean;
  country_code: string;
  message?: string;
}

export interface ArchetypeOption {
  code: string;
  label: string;
}

export interface ArchetypeOptions {
  typologie: ArchetypeOption[];
  konstruktionstyp: ArchetypeOption[];
  energieklasse: ArchetypeOption[];
}

export interface ArchetypeComputeRequest {
  address: string;
  typologie: string;
  baujahr: number;
  konstruktionstyp: number;
  energieklasse: number;
}

export interface ArchetypeComputeResponse {
  archetype_id: string;
}

// API Functions
export const uploadCSVs = async (
  productList: File,
  componentsList: File,
  buildingList: File
): Promise<CSVUploadResponse> => {
  const formData = new FormData();
  formData.append('product_list', productList);
  formData.append('components_list', componentsList);
  formData.append('building_list', buildingList);

  const response = await axiosInstance.post<CSVUploadResponse>(
    '/api/upload_csvs',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
};

export const getArchetypes = async (): Promise<ArchetypeList> => {
  const response = await axiosInstance.get<ArchetypeList>('/api/archetypes');
  return response.data;
};

export const estimateMaterials = async (
  request: MaterialEstimationRequest
): Promise<MaterialEstimationResponse> => {
  const response = await axiosInstance.post<MaterialEstimationResponse>(
    '/api/estimate_materials',
    request
  );
  return response.data;
};

export const estimateBuildingValues = async (
  request: BuildingEstimationRequest
): Promise<BuildingEstimationResponse> => {
  const response = await axiosInstance.post<BuildingEstimationResponse>(
    '/api/estimate_building_values',
    request
  );
  return response.data;
};

export const getArchetypeOptions = async (): Promise<ArchetypeOptions> => {
  const response = await axiosInstance.get<ArchetypeOptions>('/api/archetype_options');
  return response.data;
};

export const computeArchetype = async (
  request: ArchetypeComputeRequest
): Promise<ArchetypeComputeResponse> => {
  const response = await axiosInstance.post<ArchetypeComputeResponse>(
    '/api/compute_archetype',
    request
  );
  return response.data;
};

export const getRefurbishmentOptions = async (
  archetype_id: string
): Promise<RefurbishmentOptionsResponse> => {
  const response = await axiosInstance.get<RefurbishmentOptionsResponse>(
    `/api/refurbishment_options/${archetype_id}`
  );
  return response.data;
};

export const login = async (password: string): Promise<void> => {
  await axiosInstance.post('/auth/login', { password });
};

export const logout = async (): Promise<void> => {
  await axiosInstance.post('/auth/logout', {});
};

export const checkStatus = async (): Promise<{ authenticated: boolean }> => {
  try {
    const response = await axiosInstance.get<{ authenticated: boolean }>('/auth/status');
    return response.data;
  } catch (error) {
    return { authenticated: false };
  }
};
