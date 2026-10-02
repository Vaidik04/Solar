import uuid
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.modules.crm.models import CustomerType, KycStatus, PhotoCategory, RoofType, SurveyStatus
from app.modules.crm.public import (
    CustomerCreate,
    CustomerUpdate,
    SiteCreate,
    SiteSurveyCreate,
)
from app.modules.crm.events import CustomerCreated, SiteCreated, SiteSurveyCompleted


def test_customer_create_valid():
    data = CustomerCreate(
        name="Tata Power Solar Customer",
        customer_type=CustomerType.COMMERCIAL,
        phone="+919876543210",
        email="info@tatapower.example.com",
        pan_number="ABCDE1234F",
        gst_number="27ABCDE1234F1Z5",
        billing_address={"city": "Pune", "state": "MH", "pincode": "411001"},
    )
    assert data.name == "Tata Power Solar Customer"
    assert data.customer_type == CustomerType.COMMERCIAL
    assert data.phone == "+919876543210"


def test_customer_create_invalid_phone():
    with pytest.raises(ValidationError):
        CustomerCreate(
            name="Invalid User",
            phone="123",  # Too short (min 10 chars)
        )


def test_site_create_valid():
    customer_id = uuid.uuid4()
    data = SiteCreate(
        name="Rooftop Plant A - Wadala",
        customer_id=customer_id,
        state_code="MH",
        pincode="400031",
        latitude=19.0178,
        longitude=72.8478,
        discom_name="MSEDCL",
        consumer_number="000123456789",
        sanctioned_load_kw=15.0,
        roof_type=RoofType.RCC_FLAT,
        usable_roof_area_sqft=1200.0,
        tilt_angle_degrees=15.0,
        azimuth_degrees=180.0,
    )
    assert data.sanctioned_load_kw == 15.0
    assert data.usable_roof_area_sqft == 1200.0
    assert data.azimuth_degrees == 180.0


def test_site_create_invalid_angles():
    customer_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        # Tilt angle > 90 degrees
        SiteCreate(
            name="Invalid Tilt Site",
            customer_id=customer_id,
            state_code="MH",
            pincode="400031",
            discom_name="MSEDCL",
            consumer_number="000123456789",
            sanctioned_load_kw=10.0,
            usable_roof_area_sqft=500.0,
            tilt_angle_degrees=120.0,  # Invalid
        )

    with pytest.raises(ValidationError):
        # Negative sanctioned load
        SiteCreate(
            name="Invalid Load Site",
            customer_id=customer_id,
            state_code="MH",
            pincode="400031",
            discom_name="MSEDCL",
            consumer_number="000123456789",
            sanctioned_load_kw=-5.0,  # Invalid
            usable_roof_area_sqft=500.0,
        )


def test_site_survey_create():
    survey = SiteSurveyCreate(
        surveyor_user_id=uuid.uuid4(),
        survey_date=datetime.now(timezone.utc),
        structural_viability=True,
        recommended_capacity_kw=12.5,
        electrical_assessment={"grid_phase": 3, "voltage_v": 415},
        shadow_analysis={"shadow_free_hours": 6.5},
        gps_verified=True,
    )
    assert survey.structural_viability is True
    assert survey.recommended_capacity_kw == 12.5


def test_crm_domain_events():
    org_id = uuid.uuid4()
    cust_id = uuid.uuid4()

    event = CustomerCreated(
        organization_id=org_id,
        customer_id=cust_id,
        customer_type=CustomerType.RESIDENTIAL,
        name="Sunil Patil",
        phone="+919876543210",
    )
    data = event.to_dict()
    assert data["customer_id"] == str(cust_id)
    assert data["name"] == "Sunil Patil"
    assert event.event_type == "CustomerCreated"

    site_event = SiteCreated(
        organization_id=org_id,
        site_id=uuid.uuid4(),
        customer_id=cust_id,
        name="Patil Farm Solar",
        state_code="MH",
        pincode="411001",
        sanctioned_load_kw=20.0,
    )
    assert site_event.event_type == "SiteCreated"
    assert site_event.sanctioned_load_kw == 20.0
