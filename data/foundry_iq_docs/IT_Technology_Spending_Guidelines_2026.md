# Apex Digital Government Authority
## IT & Technology Spending Guidelines 2026

**Document Reference:** ADGA-IT-GUIDE-2026  
**Version:** 2.1  
**Effective Date:** January 1, 2026  
**Owner:** Office of the Chief Digital Officer  
**Approved By:** Finance Committee

---

## 1. PURPOSE AND SCOPE

These guidelines govern all IT and technology expenditures across ADGA, including:
- Software licensing and subscriptions
- Cloud computing and infrastructure
- Hardware procurement
- Cybersecurity investments
- IT professional services
- Technology training and development

---

## 2. BUDGETING PRINCIPLES

### 2.1 IT Budget Allocation
IT budgets shall be allocated across the following categories:

| Category | % of IT Budget | 2026 Benchmark |
|----------|----------------|----------------|
| Cloud & Infrastructure | 35-40% | AED 8.5M |
| Software & Licensing | 25-30% | AED 6.2M |
| Cybersecurity | 15-20% | AED 3.8M |
| Hardware & Devices | 10-15% | AED 2.9M |
| Professional Services | 10-15% | AED 2.4M |
| Training & Development | 3-5% | AED 1.0M |

### 2.2 Variable Cost Management
1. Cloud spend must be monitored monthly with auto-scaling alerts
2. Software licenses must be right-sized quarterly
3. Unused SaaS subscriptions must be cancelled within 30 days
4. Over-provisioned resources must be optimized within 60 days

---

## 3. CLOUD COMPUTING POLICIES

### 3.1 Cloud Service Provider Approval
Approved cloud platforms for ADGA:
- **Primary:** Microsoft Azure (Government Cloud)
- **Secondary:** AWS GovCloud
- **Prohibited:** Non-government-certified cloud platforms

### 3.2 Cloud Cost Control
1. **Tagging Requirements**: All resources must be tagged with:
   - Department code
   - Cost center
   - Project ID
   - Environment (prod/dev/test)

2. **Budget Alerts**:
   - Warning at 75% of monthly quota
   - Critical alert at 90% of monthly quota
   - Auto-shutdown of dev/test resources at 100%

3. **Reserved Instances**:
   - All production workloads must use reserved instances (1-3 year commitment)
   - Minimum 40% discount target vs on-demand pricing

### 3.3 Cloud Overspend Justifications
Common approved reasons for cloud overspend:
- ✅ Unexpected traffic surge (public-facing services)
- ✅ Security incident response (temporary scale-up)
- ✅ Data migration projects (one-time cost)
- ❌ Unoptimized resource sizing (requires remediation)
- ❌ Orphaned resources (requires immediate cleanup)

---

## 4. SOFTWARE LICENSING

### 4.1 Enterprise Agreements
ADGA maintains enterprise agreements with:
- Microsoft (M365, Azure, Power Platform, Dynamics)
- Adobe (Creative Cloud for Communications team)
- Atlassian (Jira, Confluence for project management)

All purchasing must leverage these agreements. Individual licenses are prohibited.

### 4.2 License Compliance
1. Annual license audit by IT Governance team
2. Shadow IT discovery scans quarterly
3. Mandatory software asset register
4. License reclamation from terminated employees within 24 hours

### 4.3 SaaS Subscription Management
1. All SaaS purchases must be approved by IT Architecture team
2. Proof of business case required for >AED 50,000/year subscriptions
3. Vendor lock-in risk assessment mandatory
4. Annual value review for all subscriptions >AED 100,000

---

## 5. CYBERSECURITY SPENDING

### 5.1 Mandatory Security Investments
The following are non-negotiable security spend categories:
1. **Endpoint Protection**: Advanced threat protection on all devices
2. **Network Security**: Firewall, IDS/IPS, DDoS protection
3. **Identity & Access**: MFA, PAM, identity governance
4. **Security Operations**: SIEM, SOC tooling, threat intelligence
5. **Data Protection**: Encryption, DLP, backup & recovery

### 5.2 Cybersecurity Budget Ring-Fencing
- Minimum 15% of IT budget must be allocated to cybersecurity
- Cybersecurity budgets cannot be reallocated to other IT categories
- Underspend in cybersecurity triggers a security posture review

### 5.3 Zero Trust Implementation (2026 Priority)
Approved overspend (up to 20%) for Zero Trust architecture components:
- Identity verification systems
- Micro-segmentation tools
- Continuous authentication platforms
- Secure access service edge (SASE) solutions

**Rationale**: National cybersecurity mandate requires Zero Trust by Q4 2026.

---

## 6. HARDWARE PROCUREMENT

### 6.1 Device Refresh Cycles
| Device Type | Standard Lifespan | Replacement Trigger |
|-------------|-------------------|---------------------|
| Laptops | 4 years | Performance degradation |
| Desktops | 5 years | End of vendor support |
| Servers | 5 years | Capacity constraints |
| Network equipment | 7 years | Security vulnerabilities |

### 6.2 Sustainable Procurement
1. Energy-efficient devices preferred (Energy Star certified)
2. Trade-in programs for old hardware
3. Repair-first policy before replacement

---

## 7. PROFESSIONAL SERVICES

### 7.1 Approved Use Cases
IT professional services may be engaged for:
- ✅ Specialized skills not available internally (e.g., AI/ML expertise)
- ✅ Peak demand periods (e.g., major system implementation)
- ✅ Independent security assessments
- ❌ Routine maintenance (must be handled internally)
- ❌ Long-term staff augmentation (use permanent hiring)

### 7.2 Rate Cards
Maximum daily rates for IT contractors:

| Role | Maximum Rate (AED/day) |
|------|------------------------|
| Junior Developer | 2,500 |
| Senior Developer | 4,500 |
| Solution Architect | 6,000 |
| Cybersecurity Specialist | 7,000 |
| AI/ML Specialist | 8,000 |

Rates exceeding these require CFO approval with justification.

---

## 8. VARIANCE ANALYSIS FOR IT SPENDING

### 8.1 Common Variance Drivers
**Acceptable variance reasons:**
1. **Cloud cost spike due to traffic surge**: Acceptable if temporary (1-2 months)
2. **Security incident response**: Acceptable with incident report
3. **Urgent system failure**: Acceptable with post-mortem
4. **Regulatory compliance deadline**: Acceptable with compliance evidence

**Unacceptable variance reasons:**
1. **Poor planning**: Budget amendment should have been requested
2. **Unapproved tool purchases**: Violation of procurement policy
3. **Inefficient resource usage**: Operational failure requiring remediation
4. **Scope creep without approval**: Project governance failure

### 8.2 IT Variance Escalation (Supersedes General Policy)
Due to the volatile nature of IT spending, IT department has modified thresholds:
- ACCEPTABLE: ≤ 10% (vs 5% standard)
- MINOR: 10-15% (vs 5-10% standard)
- SIGNIFICANT: 15-30% (vs 10-25% standard)
- CRITICAL: > 30% (vs >25% standard)

**Rationale**: IT spending includes unpredictable cloud usage and security incidents.

---

## 9. 2026 STRATEGIC PRIORITIES

### 9.1 Approved Overspend Categories for 2026
The following initiatives have pre-approved budget flexibility (+20%):
1. **Zero Trust Architecture** (National mandate)
2. **AI/ML Platform Implementation** (Strategic initiative)
3. **Cloud Migration Phase 3** (Multi-year program)

### 9.2 Cost Optimization Targets
All IT departments must achieve:
- 15% reduction in unused SaaS licenses
- 10% improvement in cloud cost efficiency
- 5% reduction in hardware refresh costs

---

## 10. REVIEW AND UPDATES

This guideline is reviewed quarterly by the IT Governance Board.  
Next review: April 1, 2026

---

**Approved by:**  
Chief Digital Officer  
Chief Financial Officer  
Director, IT Operations

