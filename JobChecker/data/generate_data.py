"""
Generates a synthetic labeled dataset of scam / legitimate job postings for
training the baseline ML classifier (SRS section 5.1-B: model selection).

NOTE: This is a small, template-based synthetic dataset meant for a working
prototype/demo. For production, replace with a real labeled corpus (e.g. the
EMSCAD - Employment Scam Aegean Dataset - referenced in the SRS) alongside
the client's own historical reports.
"""
import csv
import random
from pathlib import Path

random.seed(42)

SCAM_TEMPLATES = [
    "Urgent hiring! {role} needed immediately, apply now and start earning "
    "${amount} per week from home. No experience required. Send your bank "
    "details to receive the joining kit after paying a small registration "
    "fee of ${fee}.",

    "Congratulations! You have been selected for the {role} position. This "
    "is a limited time offer, act now! Please pay a refundable security "
    "deposit of ${fee} to confirm your slot and receive your welcome kit.",

    "We are urgently hiring {role} candidates. Earn ${amount} per day "
    "working part time. Contact us immediately at recruiter{n}@gmail.com. "
    "Processing fee of ${fee} required before joining.",

    "Immediate joining required for {role}. Hurry up, only few slots left! "
    "Send ${fee} training fee via wire transfer to secure your position and "
    "start earning ${amount} monthly.",

    "Work from home {role} opportunity! No interview needed, guaranteed "
    "job. Pay ${fee} registration fee today and receive your login "
    "credentials and starter kit within 24 hours.",

    "{role} vacancy - act now, limited seats! Earn up to ${amount} per week. "
    "A refundable kit fee of ${fee} applies. Reply to claim your spot "
    "before it's gone.",
]

LEGIT_TEMPLATES = [
    "{company} is looking for a {role} to join our growing team in {city}. "
    "The ideal candidate has {years} years of experience in the field and "
    "strong communication skills. Please submit your resume and cover "
    "letter through our careers page.",

    "We are hiring a {role} at {company}. Responsibilities include "
    "collaborating with cross-functional teams, contributing to project "
    "planning, and delivering high quality work. Competitive salary and "
    "benefits offered.",

    "{company} is expanding its {city} office and is seeking a {role}. "
    "Candidates should have a bachelor's degree and relevant experience. "
    "Interviews will be conducted over the next few weeks with our hiring "
    "panel.",

    "Join {company} as a {role}! We offer a comprehensive benefits "
    "package, professional development opportunities, and a collaborative "
    "work environment. Apply through our official website.",

    "{company} seeks an experienced {role} for our {city} team. This "
    "full-time position involves working closely with senior staff on key "
    "initiatives. Please apply with your resume via our HR portal.",

    "{company} is currently recruiting a {role} based in {city}. You will "
    "work with a small, focused team and report to the department head. "
    "We offer relocation assistance and a standard benefits package.",
]

ROLES = [
    "Data Entry Clerk", "Customer Service Representative", "Software Engineer",
    "Marketing Associate", "Sales Executive", "Administrative Assistant",
    "Graphic Designer", "Accountant", "HR Coordinator", "Content Writer",
    "Business Analyst", "Project Manager", "Warehouse Associate",
    "Virtual Assistant", "Recruiter",
]

COMPANIES = [
    "Acme Corp", "Northwind Traders", "Globex Inc", "Initech",
    "Umbrella Solutions", "Stark Industries", "Wayne Enterprises",
    "Wonka Innovations", "Hooli", "Vandelay Industries", "Pied Piper",
    "Soylent Corp",
]

CITIES = [
    "Chicago", "Austin", "Seattle", "Boston", "Denver", "Toronto",
    "London", "Bangalore", "Sydney", "Berlin", "Chennai", "Remote",
]


def generate_rows(n_per_template: int = 10):
    rows = []

    for template in SCAM_TEMPLATES:
        for i in range(n_per_template):
            text = template.format(
                role=random.choice(ROLES),
                amount=random.choice([500, 800, 1200, 1500, 2000, 3000]),
                fee=random.choice([25, 49, 75, 99, 150]),
                n=random.randint(100, 999),
            )
            rows.append({"text": text, "label": 1})

    for template in LEGIT_TEMPLATES:
        for i in range(n_per_template):
            text = template.format(
                role=random.choice(ROLES),
                company=random.choice(COMPANIES),
                city=random.choice(CITIES),
                years=random.choice([1, 2, 3, 4, 5]),
            )
            rows.append({"text": text, "label": 0})

    random.shuffle(rows)
    return rows


def main():
    rows = generate_rows(n_per_template=10)
    out_path = Path(__file__).resolve().parent / "training_data.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
