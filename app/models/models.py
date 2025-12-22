from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Archetype(Base):
    __tablename__ = "archetypes"

    archetype_id = Column(String, primary_key=True, index=True)
    country = Column(String)
    building_type = Column(String)
    construction_period_start = Column(Integer)
    construction_period_end = Column(Integer)
    main_material = Column(String)
    ref_bgf = Column(Float)  # m²
    ref_volume = Column(Float)  # m³

    elements = relationship("ArchetypeElement", back_populates="archetype")


class ElementType(Base):
    __tablename__ = "element_types"

    element_type_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, index=True)

    archetype_elements = relationship("ArchetypeElement", back_populates="element_type")


class Component(Base):
    __tablename__ = "components"

    component_id = Column(String, primary_key=True, index=True)

    products = relationship(
        "ComponentProduct", back_populates="component", cascade="all, delete-orphan"
    )
    element_components = relationship("ElementComponent", back_populates="component")


class Product(Base):
    __tablename__ = "products"

    product_id = Column(String, primary_key=True, index=True)
    designation_en = Column(String)
    category_en = Column(String)
    raw_density = Column(Float)  # kg/m³

    unit = Column(String, nullable=True)
    components = relationship("ComponentProduct", back_populates="product")


class ComponentProduct(Base):
    __tablename__ = "component_products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    component_id = Column(String, ForeignKey("components.component_id"), index=True)
    product_id = Column(String, ForeignKey("products.product_id"), index=True)
    schichtstaerke = Column(
        Float
    )  # Keep original unit (cm) for now, convert in estimation
    percentage = Column(Float)

    component = relationship("Component", back_populates="products")
    product = relationship("Product", back_populates="components")


class ArchetypeElement(Base):
    __tablename__ = "archetype_elements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    archetype_id = Column(String, ForeignKey("archetypes.archetype_id"))
    element_type_id = Column(Integer, ForeignKey("element_types.element_type_id"))
    ref_area = Column(Float)

    archetype = relationship("Archetype", back_populates="elements")
    element_type = relationship("ElementType", back_populates="archetype_elements")
    components = relationship("ElementComponent", back_populates="element")


class ElementComponent(Base):
    __tablename__ = "element_components"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    element_id = Column(Integer, ForeignKey("archetype_elements.id"))
    component_id = Column(String, ForeignKey("components.component_id"), index=True)
    refurbishment_level = Column(
        String, nullable=False, index=True, server_default="as-built"
    )

    element = relationship("ArchetypeElement", back_populates="components")
    component = relationship("Component", back_populates="element_components")
