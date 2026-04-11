"""
Pydantic models for planogram data structures and compliance results.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProductFacing(BaseModel):
    """Single product facing in a shelf section."""
    position: int
    section_id: str
    sku_id: str
    product_name: str
    expected_facings: int = 3
    price: float = 0.0
    min_stock: int = 3


class ShelfSection(BaseModel):
    """A shelf within an aisle."""
    shelf_id: str
    shelf_number: int
    sections: list[ProductFacing] = []


class Aisle(BaseModel):
    """An aisle in the store."""
    aisle_id: str
    aisle_name: str
    shelves: list[ShelfSection] = []


class Planogram(BaseModel):
    """Complete planogram definition for a store."""
    store_id: str
    store_name: str
    generated_at: str = ""
    aisles: list[Aisle] = []

    def get_section(self, aisle_id: str, shelf_id: str, section_id: str) -> Optional[ProductFacing]:
        """Look up a specific section in the planogram."""
        for aisle in self.aisles:
            if aisle.aisle_id == aisle_id:
                for shelf in aisle.shelves:
                    if shelf.shelf_id == shelf_id:
                        for section in shelf.sections:
                            if section.section_id == section_id:
                                return section
        return None

    def get_all_sections(self) -> list[ProductFacing]:
        """Get flat list of all sections."""
        sections = []
        for aisle in self.aisles:
            for shelf in aisle.shelves:
                sections.extend(shelf.sections)
        return sections

    def total_sections(self) -> int:
        return len(self.get_all_sections())


class SectionViolation(BaseModel):
    """A single planogram violation."""
    section_id: str
    violation_type: str  # 'MISPLACED', 'MISSING', 'UNAUTHORIZED', 'PRICE_MISMATCH'
    expected_sku: str = ""
    detected_sku: str = ""
    expected_price: float = 0.0
    detected_price: float = 0.0
    severity: int = 1
    message: str = ""


class ShelfComplianceResult(BaseModel):
    """Compliance result for a single shelf."""
    shelf_id: str
    compliance_score: float = 0.0
    total_sections: int = 0
    correct_sections: int = 0
    violations: list[SectionViolation] = []


class AisleComplianceResult(BaseModel):
    """Compliance result for an entire aisle."""
    aisle_id: str
    aisle_name: str = ""
    compliance_score: float = 0.0
    shelf_results: list[ShelfComplianceResult] = []
    total_violations: int = 0


class StoreComplianceReport(BaseModel):
    """Complete compliance report for a store."""
    store_id: str
    store_name: str = ""
    overall_score: float = 0.0
    aisle_results: list[AisleComplianceResult] = []
    total_sections: int = 0
    compliant_sections: int = 0
    total_misplaced: int = 0
    total_missing: int = 0
    total_unauthorized: int = 0
    total_price_mismatches: int = 0
    checked_at: str = ""
