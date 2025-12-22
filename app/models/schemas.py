from dataclasses import dataclass
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

from app.models.models import ComponentProduct, ArchetypeElement


@dataclass
class TargetAreaData:
    """
    Data class for target area data of a building component.
    """

    element_type_id: int
    element_type_name: str
    component: Tuple[ComponentProduct, ArchetypeElement]
    target_area: float
    ref_area: float


from typing import Tuple


class ProductBase(BaseModel):
    product_id: str
    designation_en: Optional[str] = None
    category_en: Optional[str] = None
    raw_density: Optional[float] = None


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    class Config:
        from_attributes = True


class ComponentProductBase(BaseModel):
    product_id: str
    schichtstaerke: float
    percentage: float


class ComponentProductCreate(ComponentProductBase):
    pass


class ComponentProduct(ComponentProductBase):
    id: int
    component_id: str

    class Config:
        from_attributes = True


class ComponentBase(BaseModel):
    component_id: str


class ComponentCreate(ComponentBase):
    pass


class Component(ComponentBase):
    products: List[ComponentProduct] = []

    class Config:
        from_attributes = True


class ElementTypeBase(BaseModel):
    name: str


class ElementTypeCreate(ElementTypeBase):
    pass


class ElementType(ElementTypeBase):
    element_type_id: int

    class Config:
        from_attributes = True


class ElementComponentBase(BaseModel):
    element_type_id: int
    component_id: str
    ref_area: float


class ElementComponentCreate(ElementComponentBase):
    pass


class ElementComponent(ElementComponentBase):
    id: int
    archetype_id: str

    class Config:
        from_attributes = True


class ArchetypeBase(BaseModel):
    archetype_id: str
    country: Optional[str] = None
    building_type: Optional[str] = None
    construction_period_start: Optional[int] = None
    construction_period_end: Optional[int] = None
    main_material: Optional[str] = None
    ref_bgf: Optional[float] = None
    ref_volume: Optional[float] = None


class ArchetypeCreate(ArchetypeBase):
    pass


class Archetype(ArchetypeBase):
    components: List[ElementComponent] = []

    class Config:
        from_attributes = True


class CSVUploadResponse(BaseModel):
    message: str
    processed_archetypes: int
    processed_element_types: int
    processed_components: int
    processed_products: int
    processed_component_products: int
    processed_archetype_elements: int
    processed_element_components: int


class ArchetypeList(BaseModel):
    archetypes: List[str]


class MaterialEstimationRequest(BaseModel):
    archetype_id: str
    target_grundflaeche: float = Field(..., gt=0)
    target_gebaeudeumrisse: float = Field(..., gt=0)
    target_gebaeudehoehe: float = Field(..., gt=0)
    refurbishment_level: str = "as-built"


class RefurbishmentOptionsResponse(BaseModel):
    archetype_id: str
    refurbishment_required: bool
    available_levels: List[str]
    default_level: Optional[str] = None
    explanation: Optional[str] = None


class MaterialByElementType(BaseModel):
    product_id: str
    product_designation: str
    element_type: str
    volume: float  # m³
    weight: float  # kg


class MaterialByProductCategory(BaseModel):
    product_id: str
    product_designation: str
    category: str
    total_volume: float  # m³
    total_weight: float  # kg


class MaterialEstimationResponse(BaseModel):
    by_element_type: List[MaterialByElementType]
    by_product_category: List[MaterialByProductCategory]
    calculation_factors: dict  # Add factors used for transparency
    window_data: List[Tuple[str, str, float]] = []
