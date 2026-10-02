"""
Solar Operations OS — CRM & Sites Module: Database Models
Owns: Customer, Contact, Site, SiteSurvey, SitePhoto
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, SoftDeleteMixin, TenantMixin, TimestampMixin, VersionMixin


# ── Enums ─────────────────────────────────────────────────────────────────────
class CustomerType(StrEnum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    INSTITUTIONAL = "institutional"
    AGRICULTURAL = "agricultural"


class KycStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXEMPT = "exempt"


class RoofType(StrEnum):
    RCC_FLAT = "rcc_flat"
    METAL_SHEET = "metal_sheet"
    TILED = "tiled"
    GROUND_MOUNT = "ground_mount"
    ELEVATED_STRUCTURE = "elevated_structure"
    HYBRID = "hybrid"


class SurveyStatus(StrEnum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"


class PhotoCategory(StrEnum):
    ROOF = "roof"
    METER_BOARD = "meter_board"
    TRANSFORMER = "transformer"
    DISTRIBUTION_BOX = "distribution_box"
    INVERTER_LOCATION = "inverter_location"
    CABLE_TRAY_ROUTE = "cable_tray_route"
    SHADOW_OBSTACLE = "shadow_obstacle"
    EARTHING_PIT = "earthing_pit"
    ACCESS_ROUTE = "access_route"
    OTHER = "other"


# ── Customer ──────────────────────────────────────────────────────────────────
class Customer(Base, TenantMixin, TimestampMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "customer"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_type: Mapped[str] = mapped_column(String(50), nullable=False, default=CustomerType.RESIDENTIAL)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    alternate_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Compliance & Tax Identifiers
    pan_number: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    gst_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    kyc_status: Mapped[str] = mapped_column(String(50), nullable=False, default=KycStatus.PENDING)

    # Billing Address
    billing_address: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    contacts: Mapped[list[Contact]] = relationship("Contact", back_populates="customer", cascade="all, delete-orphan")
    sites: Mapped[list[Site]] = relationship("Site", back_populates="customer")

    __table_args__ = (
        Index("ix_customer_org_phone", "organization_id", "phone"),
        Index("ix_customer_org_email", "organization_id", "email"),
        Index("ix_customer_org_name", "organization_id", "name"),
    )


# ── Contact ───────────────────────────────────────────────────────────────────
class Contact(Base, TenantMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "contact"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    designation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    customer: Mapped[Customer] = relationship("Customer", back_populates="contacts")

    __table_args__ = (
        Index("ix_contact_customer", "customer_id"),
        Index("ix_contact_org", "organization_id"),
    )


# ── Site ──────────────────────────────────────────────────────────────────────
class Site(Base, TenantMixin, TimestampMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "site"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer.id", ondelete="RESTRICT"), nullable=False
    )
    branch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branch.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    state_code: Mapped[str] = mapped_column(String(10), nullable=False)  # e.g., "MH", "GJ", "KA"
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)

    # Geolocation Coordinates
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Electrical & Utility Data
    discom_name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "MSEDCL", "BESCOM", "TATA_POWER"
    consumer_number: Mapped[str] = mapped_column(String(100), nullable=False)  # Encrypted at field-level or indexed hash
    meter_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sanctioned_load_kw: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    tariff_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., "LT-Residential", "HT-Commercial"
    transformer_capacity_kva: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    supply_voltage_kv: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True, default=0.415)  # 0.415 kV = 415V 3-phase

    # Roof & Structural Characteristics
    roof_type: Mapped[str] = mapped_column(String(50), nullable=False, default=RoofType.RCC_FLAT)
    usable_roof_area_sqft: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    tilt_angle_degrees: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    azimuth_degrees: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True, default=180.0)  # 180° = South facing
    shading_hazards: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)

    # Relationships
    customer: Mapped[Customer] = relationship("Customer", back_populates="sites")
    surveys: Mapped[list[SiteSurvey]] = relationship("SiteSurvey", back_populates="site", cascade="all, delete-orphan")
    photos: Mapped[list[SitePhoto]] = relationship("SitePhoto", back_populates="site", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_site_org_customer", "organization_id", "customer_id"),
        Index("ix_site_org_consumer_num", "organization_id", "consumer_number"),
        Index("ix_site_org_state_pincode", "organization_id", "state_code", "pincode"),
    )


# ── Site Survey ───────────────────────────────────────────────────────────────
class SiteSurvey(Base, TenantMixin, TimestampMixin, VersionMixin):
    __tablename__ = "site_survey"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("site.id", ondelete="CASCADE"), nullable=False
    )
    surveyor_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=SurveyStatus.SCHEDULED)
    survey_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Survey Evaluation & Findings
    structural_viability: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    recommended_capacity_kw: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    electrical_assessment: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    shadow_analysis: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    gps_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    survey_coordinates: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    site: Mapped[Site] = relationship("Site", back_populates="surveys")

    __table_args__ = (
        Index("ix_site_survey_site", "site_id"),
        Index("ix_site_survey_org_status", "organization_id", "status"),
    )


# ── Site Photo ────────────────────────────────────────────────────────────────
class SitePhoto(Base, TenantMixin, TimestampMixin):
    __tablename__ = "site_photo"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("site.id", ondelete="CASCADE"), nullable=False
    )
    survey_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("site_survey.id", ondelete="SET NULL"), nullable=True
    )
    uploader_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False
    )

    category: Mapped[str] = mapped_column(String(50), nullable=False, default=PhotoCategory.ROOF)
    caption: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Content-Addressed Storage Reference (ADR-007)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False, default="image/jpeg")

    # Verified EXIF Geo & Timestamp Metadata
    exif_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    exif_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    exif_captured_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    compass_bearing_degrees: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)

    site: Mapped[Site] = relationship("Site", back_populates="photos")

    __table_args__ = (
        Index("ix_site_photo_site", "site_id"),
        Index("ix_site_photo_sha256", "organization_id", "sha256_hash"),
    )
