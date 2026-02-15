"""
Denver CO Sample Data Generator
Generates realistic tenant, property, lease, payment, and maintenance data
for the Denver metro area (80,000+ properties)
"""

import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

# Denver Metro ZIP codes and neighborhoods
DENVER_ZIPCODES = {
    "80202": {"neighborhood": "Downtown Denver", "avg_rent": 2800, "vacancy": 0.05},
    "80203": {"neighborhood": "Capitol Hill", "avg_rent": 2200, "vacancy": 0.06},
    "80204": {"neighborhood": "Highlands", "avg_rent": 2600, "vacancy": 0.04},
    "80205": {"neighborhood": "RiNo", "avg_rent": 2500, "vacancy": 0.05},
    "80206": {"neighborhood": "Park Hill", "avg_rent": 2100, "vacancy": 0.07},
    "80209": {"neighborhood": "Cherry Creek", "avg_rent": 3200, "vacancy": 0.03},
    "80210": {"neighborhood": "Washington Park", "avg_rent": 2900, "vacancy": 0.04},
    "80211": {"neighborhood": "Berkeley", "avg_rent": 2400, "vacancy": 0.05},
    "80212": {"neighborhood": "Lakewood", "avg_rent": 2000, "vacancy": 0.08},
    "80218": {"neighborhood": "Congress Park", "avg_rent": 2300, "vacancy": 0.06},
    "80220": {"neighborhood": "Stapleton", "avg_rent": 2400, "vacancy": 0.05},
    "80221": {"neighborhood": "Northglenn", "avg_rent": 1900, "vacancy": 0.09},
    "80222": {"neighborhood": "Glendale", "avg_rent": 2100, "vacancy": 0.07},
    "80224": {"neighborhood": "Aurora Central", "avg_rent": 1800, "vacancy": 0.10},
    "80226": {"neighborhood": "Edgewater", "avg_rent": 2200, "vacancy": 0.06},
    "80227": {"neighborhood": "Littleton", "avg_rent": 2000, "vacancy": 0.07},
    "80230": {"neighborhood": "DTC", "avg_rent": 2700, "vacancy": 0.04},
    "80231": {"neighborhood": "Cherry Creek South", "avg_rent": 3000, "vacancy": 0.03},
    "80235": {"neighborhood": "Ken Caryl", "avg_rent": 2500, "vacancy": 0.05},
    "80246": {"neighborhood": "South Denver", "avg_rent": 2400, "vacancy": 0.05},
}

STREET_NAMES = [
    "Main",
    "Oak",
    "Maple",
    "Pine",
    "Cedar",
    "Elm",
    "Washington",
    "Lincoln",
    "Park",
    "Lake",
    "Hill",
    "Sunset",
    "Meadow",
    "River",
    "Forest",
    "Mountain",
]

STREET_TYPES = ["St", "Ave", "Dr", "Ln", "Way", "Ct", "Pl", "Cir"]

FIRST_NAMES = [
    "James",
    "Mary",
    "John",
    "Patricia",
    "Robert",
    "Jennifer",
    "Michael",
    "Linda",
    "William",
    "Elizabeth",
    "David",
    "Barbara",
    "Richard",
    "Susan",
    "Joseph",
    "Jessica",
    "Thomas",
    "Sarah",
    "Christopher",
    "Karen",
    "Daniel",
    "Nancy",
    "Matthew",
    "Lisa",
    "Anthony",
    "Betty",
    "Mark",
    "Margaret",
    "Donald",
    "Sandra",
    "Steven",
    "Ashley",
    "Paul",
    "Kimberly",
    "Andrew",
    "Emily",
    "Joshua",
    "Donna",
    "Kenneth",
    "Michelle",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
    "Martin",
    "Lee",
    "Thompson",
    "White",
    "Harris",
    "Sanchez",
    "Clark",
    "Ramirez",
    "Lewis",
    "Robinson",
    "Walker",
    "Young",
]


class DenverDataGenerator:
    """Generate realistic Denver metro area tenant and property data"""

    def __init__(self, num_properties: int = 80000):
        self.num_properties = num_properties
        self.properties = []
        self.tenants = []
        self.leases = []
        self.payments = []
        self.maintenance = []

    def generate_all(self):
        """Generate all datasets"""
        print(f"Generating data for {self.num_properties} properties...")

        self.generate_properties()
        self.generate_tenants()
        self.generate_leases()
        self.generate_payments()
        self.generate_maintenance()

        print(f"Generated:")
        print(f"  - {len(self.properties)} properties")
        print(f"  - {len(self.tenants)} tenants")
        print(f"  - {len(self.leases)} leases")
        print(f"  - {len(self.payments)} payments")
        print(f"  - {len(self.maintenance)} maintenance requests")

    def generate_properties(self):
        """Generate property data"""
        print("Generating properties...")

        for i in range(self.num_properties):
            zip_code = random.choice(list(DENVER_ZIPCODES.keys()))
            zip_info = DENVER_ZIPCODES[zip_code]

            # Generate address
            street_num = random.randint(100, 9999)
            street_name = random.choice(STREET_NAMES)
            street_type = random.choice(STREET_TYPES)
            address = f"{street_num} {street_name} {street_type}"

            # Property characteristics
            bedrooms = random.choices([2, 3, 4, 5], weights=[0.2, 0.5, 0.25, 0.05])[0]
            bathrooms = random.choices(
                [1.0, 1.5, 2.0, 2.5, 3.0], weights=[0.1, 0.2, 0.4, 0.2, 0.1]
            )[0]

            # Square footage based on bedrooms
            base_sqft = {2: 1200, 3: 1600, 4: 2200, 5: 2800}[bedrooms]
            square_feet = base_sqft + random.randint(-200, 400)

            # Year built (Denver properties range from 1950s to present)
            year_built = random.randint(1950, 2023)
            property_age = 2024 - year_built

            property = {
                "property_id": f"PROP-{i + 1:06d}",
                "address": address,
                "city": "Denver",
                "state": "CO",
                "zip_code": zip_code,
                "neighborhood": zip_info["neighborhood"],
                "square_feet": square_feet,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "year_built": year_built,
                "property_age": property_age,
                "property_type": "single-family",
                "has_garage": random.random() > 0.3,
                "has_yard": random.random() > 0.2,
                "has_ac": random.random() > 0.4,
                "condition_rating": max(1, min(5, int(random.gauss(4, 1)))),
                "location_score": max(1, min(10, int(random.gauss(7, 2)))),
                "school_rating": max(1, min(10, int(random.gauss(6, 2)))),
                "latitude": 39.7392 + random.uniform(-0.1, 0.1),
                "longitude": -104.9903 + random.uniform(-0.1, 0.1),
                "market_rent_median": zip_info["avg_rent"],
                "vacancy_rate": zip_info["vacancy"],
            }

            self.properties.append(property)

    def generate_tenants(self):
        """Generate tenant data (one per property)"""
        print("Generating tenants...")

        for i in range(self.num_properties):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)

            tenant = {
                "tenant_id": f"TENANT-{i + 1:06d}",
                "first_name": first_name,
                "last_name": last_name,
                "email": f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@email.com",
                "phone": f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
                "date_of_birth": (
                    datetime.now() - timedelta(days=random.randint(25 * 365, 65 * 365))
                )
                .date()
                .isoformat(),
                "household_size": random.choices(
                    [1, 2, 3, 4, 5], weights=[0.3, 0.35, 0.2, 0.1, 0.05]
                )[0],
                "annual_income": random.randint(40000, 150000),
                "employment_status": random.choices(
                    ["employed", "self-employed", "retired"], weights=[0.8, 0.15, 0.05]
                )[0],
                "account_created_at": (
                    datetime.now() - timedelta(days=random.randint(1, 1800))
                ).isoformat(),
                "portal_login_count": random.randint(5, 100),
                "last_login_at": (
                    datetime.now() - timedelta(days=random.randint(1, 60))
                ).isoformat(),
                "autopay_enabled": random.random() > 0.4,
                "primary_payment_method": random.choices(
                    ["ach", "credit-card", "debit-card"], weights=[0.5, 0.3, 0.2]
                )[0],
                "avg_response_time_hours": max(1, int(random.gauss(24, 12))),
                "complaint_count": random.choices(
                    [0, 1, 2, 3], weights=[0.7, 0.2, 0.08, 0.02]
                )[0],
                "status": "active",
            }

            self.tenants.append(tenant)

    def generate_leases(self):
        """Generate lease data"""
        print("Generating leases...")

        today = datetime.now()

        for i in range(self.num_properties):
            property_data = self.properties[i]
            tenant_data = self.tenants[i]

            # Lease start date (past 0-36 months)
            start_date = today - timedelta(days=random.randint(0, 1095))
            lease_term = random.choices([12, 24], weights=[0.9, 0.1])[0]
            end_date = start_date + timedelta(days=lease_term * 30)

            # Calculate rent based on property and market
            base_rent = property_data["market_rent_median"]
            sqft_factor = property_data["square_feet"] / 1600
            rent_variance = random.uniform(0.9, 1.1)
            monthly_rent = (
                int(base_rent * sqft_factor * rent_variance / 50) * 50
            )  # Round to $50

            # Churn factors (for realistic label generation)
            churn_probability = self._calculate_churn_probability(
                property_data, tenant_data, monthly_rent, start_date, end_date
            )

            lease = {
                "lease_id": f"LEASE-{i + 1:06d}",
                "tenant_id": tenant_data["tenant_id"],
                "property_id": property_data["property_id"],
                "start_date": start_date.date().isoformat(),
                "end_date": end_date.date().isoformat(),
                "lease_term_months": lease_term,
                "monthly_rent": monthly_rent,
                "security_deposit": monthly_rent * random.choice([1, 1.5, 2]),
                "renewal_status": self._determine_renewal_status(
                    end_date, churn_probability
                ),
                "renewal_count": random.randint(0, 5),
                "last_rent_increase_pct": round(random.uniform(0, 0.08), 3),
                "status": "active" if end_date > today else "expired",
                "churn_probability": churn_probability,  # For training labels
                "days_to_expiration": (end_date - today).days,
            }

            self.leases.append(lease)

    def _calculate_churn_probability(
        self,
        property_data: Dict,
        tenant_data: Dict,
        monthly_rent: float,
        start_date: datetime,
        end_date: datetime,
    ) -> float:
        """Calculate realistic churn probability based on features"""

        score = 0.3  # Base probability

        # Payment behavior
        if not tenant_data["autopay_enabled"]:
            score += 0.1
        if tenant_data["complaint_count"] > 1:
            score += 0.15

        # Property condition
        if property_data["condition_rating"] < 3:
            score += 0.1
        if property_data["property_age"] > 40:
            score += 0.05

        # Rent to market ratio
        rent_ratio = monthly_rent / property_data["market_rent_median"]
        if rent_ratio > 1.1:
            score += 0.15
        elif rent_ratio < 0.9:
            score -= 0.1

        # Tenure (longer tenure = lower churn)
        tenure_months = (datetime.now() - start_date).days / 30
        if tenure_months > 24:
            score -= 0.1
        elif tenure_months < 6:
            score += 0.1

        # Market conditions
        if property_data["vacancy_rate"] > 0.07:
            score -= 0.05  # High supply = less likely to churn

        return min(max(score, 0), 1)

    def _determine_renewal_status(self, end_date: datetime, churn_prob: float) -> str:
        """Determine renewal status based on end date and churn probability"""
        days_to_expiration = (end_date - datetime.now()).days

        if days_to_expiration > 90:
            return "active"
        elif days_to_expiration > 0:
            return "pending-renewal"
        else:
            # Use churn probability to determine outcome
            if random.random() < churn_prob:
                return "not-renewed"
            else:
                return "renewed"

    def generate_payments(self):
        """Generate payment history"""
        print("Generating payment history...")

        payment_id = 1
        for lease in self.leases:
            start_date = datetime.fromisoformat(lease["start_date"])
            end_date = datetime.fromisoformat(lease["end_date"])
            monthly_rent = lease["monthly_rent"]

            # Generate payments for each month
            current_date = start_date
            while current_date < min(end_date, datetime.now()):
                # Payment behavior based on churn probability
                is_late = random.random() < (lease["churn_probability"] * 0.5)
                days_late = random.randint(1, 15) if is_late else 0
                payment_date = current_date + timedelta(days=days_late)

                payment = {
                    "payment_id": f"PAY-{payment_id:08d}",
                    "lease_id": lease["lease_id"],
                    "payment_date": payment_date.date().isoformat(),
                    "amount": monthly_rent,
                    "payment_method": self.tenants[
                        int(lease["tenant_id"].split("-")[1]) - 1
                    ]["primary_payment_method"],
                    "days_late": days_late,
                    "late_fee": 50 if days_late > 5 else 0,
                    "status": "completed",
                }

                self.payments.append(payment)
                payment_id += 1
                current_date += timedelta(days=30)

    def generate_maintenance(self):
        """Generate maintenance requests"""
        print("Generating maintenance requests...")

        request_id = 1
        for lease in self.leases:
            # Number of maintenance requests based on property age and condition
            property = next(
                p for p in self.properties if p["property_id"] == lease["property_id"]
            )

            avg_requests = max(0, int(random.gauss(2, 1)))
            if property["property_age"] > 30:
                avg_requests += 1
            if property["condition_rating"] < 3:
                avg_requests += 2

            for _ in range(avg_requests):
                request_date = datetime.fromisoformat(lease["start_date"]) + timedelta(
                    days=random.randint(0, 300)
                )

                if request_date > datetime.now():
                    continue

                resolution_days = random.randint(1, 14)
                resolution_date = request_date + timedelta(days=resolution_days)

                request = {
                    "request_id": f"MAINT-{request_id:08d}",
                    "property_id": lease["property_id"],
                    "lease_id": lease["lease_id"],
                    "request_date": request_date.date().isoformat(),
                    "request_type": random.choice(
                        [
                            "HVAC",
                            "Plumbing",
                            "Electrical",
                            "Appliance",
                            "Roof",
                            "Windows",
                            "Landscaping",
                            "Pest Control",
                            "General Repair",
                        ]
                    ),
                    "priority": random.choices(
                        ["LOW", "MEDIUM", "HIGH"], weights=[0.6, 0.3, 0.1]
                    )[0],
                    "status": "completed",
                    "resolution_date": resolution_date.date().isoformat(),
                    "resolution_days": resolution_days,
                    "cost": random.randint(50, 1000),
                }

                self.maintenance.append(request)
                request_id += 1

    def save_to_csv(self, output_dir: Path):
        """Save all datasets to CSV files"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\nSaving data to {output_dir}...")

        # Save properties
        with open(output_dir / "properties.csv", "w", newline="") as f:
            if self.properties:
                writer = csv.DictWriter(f, fieldnames=self.properties[0].keys())
                writer.writeheader()
                writer.writerows(self.properties)

        # Save tenants
        with open(output_dir / "tenants.csv", "w", newline="") as f:
            if self.tenants:
                writer = csv.DictWriter(f, fieldnames=self.tenants[0].keys())
                writer.writeheader()
                writer.writerows(self.tenants)

        # Save leases
        with open(output_dir / "leases.csv", "w", newline="") as f:
            if self.leases:
                writer = csv.DictWriter(f, fieldnames=self.leases[0].keys())
                writer.writeheader()
                writer.writerows(self.leases)

        # Save payments
        with open(output_dir / "payments.csv", "w", newline="") as f:
            if self.payments:
                writer = csv.DictWriter(f, fieldnames=self.payments[0].keys())
                writer.writeheader()
                writer.writerows(self.payments)

        # Save maintenance
        with open(output_dir / "maintenance.csv", "w", newline="") as f:
            if self.maintenance:
                writer = csv.DictWriter(f, fieldnames=self.maintenance[0].keys())
                writer.writeheader()
                writer.writerows(self.maintenance)

        print("Data saved successfully!")


if __name__ == "__main__":
    # Generate sample dataset (use 1000 for testing, 80000 for full dataset)
    generator = DenverDataGenerator(num_properties=1000)
    generator.generate_all()

    # Save to CSV
    output_path = Path(__file__).parent.parent.parent / "data" / "raw" / "denver_sample"
    generator.save_to_csv(output_path)

    print(f"\n{'=' * 60}")
    print("Sample data generation complete!")
    print(f"{'=' * 60}")
    print(f"\nFiles saved to: {output_path}")
    print("\nTo generate full 80,000 property dataset, run:")
    print("  python generate_denver_data.py --full")
