"""FROGÉ HQ full agent roster — ONE template + this data table.

115 employees defined as DATA (name, role, department, specialty). Idle employees
are just rows here — zero CPU, zero RAM, until Maya routes a task to them.
The Prompt Compiler (app/prompts/compiler.py) fills the universal template with
a row from this table at runtime. No per-employee prompt files needed.

Only the 5 seeded in registry.py are real running code today. The rest activate
on demand via the roster.
"""
from __future__ import annotations

# (id, name, role, department, specialty_one_line)
ROSTER: list[dict] = []


def _add(id: str, name: str, role: str, department: str, specialty: str) -> None:
    ROSTER.append({
        "id": id, "name": name, "role": role,
        "department": department, "specialty": specialty,
    })


# 1. Software Engineering — Lead: Alex
_add("alex", "Alex", "Software Engineering Lead", "software_engineering", "Full-stack builds, code architecture, real implementation")
_add("nova-fe", "Nova", "Frontend Engineer", "software_engineering", "React/UI, components, client-side work")
_add("backend-max", "Backend-Max", "Backend Engineer", "software_engineering", "APIs, services, server logic")
_add("rust-engine", "Rust-Engine", "Systems/Rust Engineer", "software_engineering", "Low-level systems, performance-critical code")
_add("jax", "Jax", "React & UI Engineer", "software_engineering", "React apps, state, interactive UIs")
_add("db-architect", "DB-Architect", "Database Engineer", "software_engineering", "Schema design, queries, data integrity")
_add("tree-sitter", "Tree-Sitter", "AST/Code Intelligence", "software_engineering", "Code parsing, static analysis")
_add("git-ops", "Git-Ops", "Git & Release Engineer", "software_engineering", "Branching, releases, version control")
_add("legacy-refactor", "Legacy-Refactor", "Code Modernization", "software_engineering", "Refactoring legacy systems safely")
_add("algo-opt", "Algo-Opt", "Performance Engineer", "software_engineering", "Profiling, optimization, algorithms")

# 2. Marketing & Growth — Lead: Mira
_add("mira", "Mira", "Marketing Director", "marketing", "Marketing strategy, brand growth")
_add("brand-x", "Brand-X", "Brand Strategist", "marketing", "Brand identity and positioning")
_add("adrian", "Adrian", "Campaign Planner", "marketing", "Campaign planning and execution")
_add("vera", "Vera", "Social Media Strategist", "marketing", "Social channels and engagement")
_add("trend", "Trend", "Market Trends Analyst", "marketing", "Market research and trend analysis")
_add("growth", "Growth", "Growth Optimization Agent", "marketing", "Growth loops and funnel optimization")
_add("copymax", "CopyMax", "Marketing Copywriter", "marketing", "Persuasive marketing copy")
_add("audience", "Audience", "Customer Researcher", "marketing", "Customer personas and research")
_add("launch", "Launch", "Product Launch Specialist", "marketing", "Go-to-market launches")
_add("analytics-m", "Analytics", "Marketing Analytics Agent", "marketing", "Marketing metrics and attribution")

# 3. Space & Aerospace — Lead: Orion
_add("orion", "Orion", "Aerospace Lead", "aerospace", "Space systems and mission planning")
_add("nova-s", "Nova-S", "Space Systems Engineer", "aerospace", "Spacecraft and space systems design")
_add("atlas", "Atlas", "Rocket Systems Researcher", "aerospace", "Launch vehicle systems")
_add("luna", "Luna", "Lunar Mission Researcher", "aerospace", "Lunar exploration and missions")
_add("mars", "Mars", "Mars Mission Researcher", "aerospace", "Mars exploration and missions")
_add("orbit", "Orbit", "Orbital Mechanics Researcher", "aerospace", "Orbital dynamics and trajectories")
_add("rover", "Rover", "Planetary Robotics Engineer", "aerospace", "Planetary rovers and robotics")
_add("propel", "Propel", "Propulsion Researcher", "aerospace", "Rocket propulsion systems")
_add("astro", "Astro", "Astronomy Researcher", "aerospace", "Astronomy and observation")
_add("cosmos", "Cosmos", "Future Space Technology", "aerospace", "Emerging space technologies")

# 4. AI Research & Intelligence — Lead: Sarah
_add("sarah", "Sarah", "AI Research Lead", "ai_research", "AI/ML research direction")
_add("paper", "Paper", "Research Paper Analyst", "ai_research", "Reading and synthesizing papers")
_add("model-x", "Model-X", "Model Researcher", "ai_research", "Model architectures and capabilities")
_add("vision", "Vision", "Computer Vision Researcher", "ai_research", "Image/video understanding models")
_add("neural", "Neural", "Neural Architecture Researcher", "ai_research", "Neural network design")
_add("memory-ai", "Memory", "AI Memory Researcher", "ai_research", "Agent memory and retrieval")
_add("reason", "Reason", "Reasoning Researcher", "ai_research", "LLM reasoning methods")
_add("datamind", "DataMind", "Dataset Researcher", "ai_research", "Training data and datasets")
_add("eval", "Eval", "AI Evaluation Specialist", "ai_research", "Model evaluation and benchmarks")
_add("future", "Future", "Emerging AI Technology Scout", "ai_research", "Tracking new AI capabilities")

# 5. Creative, 3D & Media — Lead: Leo
_add("leo", "Leo", "Creative Director", "creative", "Creative vision and direction")
_add("blender-x", "Blender-X", "3D Artist", "creative", "3D modeling and scenes")
_add("pixel", "Pixel", "Pixel/Office Designer", "creative", "Pixel art and office visuals")
_add("motion", "Motion", "Animation Specialist", "creative", "Motion graphics and animation")
_add("vision-art", "Vision-Art", "Visual Concept Artist", "creative", "Concept art and visual design")
_add("figma-sync", "Figma-Sync", "UI Designer", "creative", "UI design systems")
_add("render", "Render", "Rendering/Shader Engineer", "creative", "Rendering pipelines and shaders")
_add("audio", "Audio", "Audio Designer", "creative", "Sound and audio design")
_add("cinematic", "Cinematic", "Cinematic Director", "creative", "Cinematic visuals and storytelling")
_add("asset", "Asset", "Digital Asset Producer", "creative", "Digital asset pipelines")

# 6. Research, Science & Knowledge — Lead: Iris
_add("iris", "Iris", "Research Director", "research", "Research direction and synthesis")
_add("fact-x", "Fact-X", "Fact Checker", "research", "Verifying claims against sources")
_add("science", "Science", "General Science Researcher", "research", "Broad scientific research")
_add("physics", "Physics", "Physics Researcher", "research", "Physics topics and analysis")
_add("chem", "Chem", "Chemistry Researcher", "research", "Chemistry topics and analysis")
_add("bio", "Bio", "Biology Researcher", "research", "Biology topics and analysis")
_add("techscout", "TechScout", "Technology Researcher", "research", "Emerging technology research")
_add("docu", "Docu", "Documentation Researcher", "research", "Docs, references, manuals")
_add("citation", "Citation", "Source Verification Specialist", "research", "Source and citation checking")
_add("knowledge", "Knowledge", "Knowledge Graph Engineer", "research", "Knowledge graphs and linking")

# 7. QA, Security & Safety — Leads: Sam & Rex
_add("sam", "Sam", "QA Director", "qa", "Testing strategy, verification, QA evidence")
_add("rex", "Rex", "Security/Gatekeeper Lead", "security", "Policy enforcement, threat review")
_add("unit", "Unit", "Unit-Test Engineer", "qa", "Unit tests and coverage")
_add("e2e", "E2E", "End-to-End Tester", "qa", "Full-flow and integration testing")
_add("vuln", "Vuln", "Vulnerability Auditor", "security", "Vulnerability scanning and audit")
_add("secret", "Secret", "Secret/Key Leak Detector", "security", "Detecting leaked credentials")
_add("redteam", "RedTeam", "Defensive Security Tester", "security", "Adversarial testing")
_add("regression", "Regression", "Regression Tester", "qa", "Preventing regressions")
_add("sandbox", "Sandbox", "Sandbox Engineer", "security", "Safe execution environments")
_add("safety", "Safety", "AI Safety Auditor", "security", "AI behavior safety review")

# 8. DevOps, Infrastructure & Hardware — Lead: Kai
_add("kai", "Kai", "DevOps Lead", "devops", "Infrastructure and operations")
_add("container", "Container", "Container Engineer", "devops", "Docker, containers, images")
_add("network", "Network", "Network Engineer", "devops", "Networking and connectivity")
_add("process", "Process", "Process/Resource Manager", "devops", "Processes and resource limits")
_add("cloud", "Cloud", "Cloud Infrastructure Engineer", "devops", "Cloud platforms and services")
_add("ci-cd", "CI-CD", "Deployment Engineer", "devops", "CI/CD pipelines and deploys")
_add("hardware", "Hardware", "Hardware Integration Engineer", "devops", "Hardware interfaces")
_add("esp", "ESP", "ESP32/IoT Engineer", "devops", "ESP32 and IoT devices")
_add("thermal", "Thermal", "Thermal & Power Monitor", "devops", "Thermal and power monitoring")
_add("recovery", "Recovery", "Infrastructure Recovery Engineer", "devops", "Failure recovery and resilience")

# 9. Business, Product & Operations — Leads: Maya & Elena
_add("maya", "Maya", "Chief Architect / Executive Orchestrator", "orchestration", "Org-wide orchestration and planning")
_add("elena", "Elena", "Operations Director", "operations", "Operations and resource management")
_add("product", "Product", "Product Manager", "operations", "Product roadmap and priorities")
_add("finance", "Finance", "FinOps Analyst", "operations", "Cost and financial operations")
_add("sla", "SLA", "Reliability & SLA Manager", "operations", "Uptime and reliability targets")
_add("license", "License", "License/Compliance Auditor", "operations", "Licensing and compliance")
_add("metrics", "Metrics", "Business Analytics Agent", "operations", "Business metrics and reporting")
_add("backlog", "Backlog", "Product Backlog Manager", "operations", "Backlog grooming and ordering")
_add("standup", "Standup", "Daily Briefing Manager", "operations", "Daily summaries and briefings")
_add("strategy", "Strategy", "Long-Term Strategy Researcher", "operations", "Long-range strategy")

# 10. Client & Web Services — Lead: Casey
_add("casey", "Casey", "Client Relations Lead", "client_services", "Client relationships and delivery")
_add("outreach", "Outreach", "LinkedIn Prospecting Agent", "client_services", "Prospecting and outreach")
_add("pitch", "Pitch", "Proposal & Pitch Writer", "client_services", "Proposals and pitches")
_add("mailer", "Mailer", "Email Communication Specialist", "client_services", "Email drafting and comms")
_add("websmith", "WebSmith", "Website Builder", "client_services", "Building client websites")
_add("reviser", "Reviser", "Website Editing & Revision Agent", "client_services", "Website edits and revisions")
_add("onboard", "Onboard", "Client Onboarding Specialist", "client_services", "Client onboarding flow")
_add("invoice", "Invoice", "Billing & Invoicing Agent", "client_services", "Billing and invoices")
_add("feedback", "Feedback", "Client Feedback Tracker", "client_services", "Client satisfaction tracking")
_add("portfolio", "Portfolio", "Case Study & Portfolio Builder", "client_services", "Case studies and portfolio")
_add("uxflow", "UXFlow", "UI/UX Design Specialist", "client_services", "UI/UX design")
_add("qa-client", "QA-Client", "Client-Facing Testing Agent", "client_services", "Client-facing QA")
_add("seo-pulse", "SEO-Pulse", "SEO & Performance Auditor", "client_services", "SEO and site performance")
_add("retain", "Retain", "Care Plan / Retainer Manager", "client_services", "Retainers and care plans")
_add("rescue", "Rescue", "Bug-Fix / Website Rescue Specialist", "client_services", "Fixing broken websites")
_add("scope", "Scope", "Project Scoping & Pricing Agent", "client_services", "Scoping and pricing work")

# 11. Machine Learning & Data Science — Lead: Quinn
_add("quinn", "Quinn", "ML Lead", "ml_data", "ML strategy and delivery")
_add("datasci", "DataSci", "Data Scientist", "ml_data", "Data science and analysis")
_add("cleanse", "Cleanse", "Data Cleaning & Preprocessing", "ml_data", "Data cleaning and prep")
_add("feature", "Feature", "Feature Engineering Specialist", "ml_data", "Feature engineering")
_add("pipeline", "Pipeline", "Data Pipeline Engineer", "ml_data", "Data pipelines and ETL")
_add("modeltrain", "ModelTrain", "Model Training Specialist", "ml_data", "Model training runs")
_add("label", "Label", "Data Labeling & Annotation Agent", "ml_data", "Labeling and annotation")
_add("stat", "Stat", "Statistical Analyst", "ml_data", "Statistics and inference")
_add("viz", "Viz", "Data Visualization Specialist", "ml_data", "Charts and visualizations")
_add("mlops", "MLOps", "Model Deployment & Monitoring", "ml_data", "Model deployment and monitoring")


def by_id(employee_id: str) -> dict | None:
    return next((r for r in ROSTER if r["id"] == employee_id), None)


def by_department(department: str) -> list[dict]:
    return [r for r in ROSTER if r["department"] == department]


def leads() -> list[dict]:
    lead_ids = {"alex", "mira", "orion", "sarah", "leo", "iris", "sam", "rex", "kai", "maya", "elena", "casey", "quinn"}
    return [r for r in ROSTER if r["id"] in lead_ids]
