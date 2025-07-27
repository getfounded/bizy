# Comprehensive Business Logic Use Case Catalogue

## **E-Commerce & Retail**

### **Dynamic Pricing Engine**
**Business Context:** Online retailer needs to adjust prices in real-time based on demand, inventory levels, competitor pricing, and customer segments.

**Business Logic:**
- If inventory < 10 units AND demand_score > 0.8, increase price by 5-15%
- If competitor_price < our_price BY more than 10%, trigger price review
- Premium customers get 5% discount on all items
- Bulk orders (>50 units) get tiered discounts: 10%, 15%, 20%

**Implementation Example:**
```
RULE: Dynamic_Pricing_Adjustment
IF product.inventory_level <= 10 
   AND product.demand_score >= 0.8 
   AND product.margin >= 0.3
THEN apply_price_increase(product, 0.05 to 0.15)

IF customer.tier == "PREMIUM"
THEN apply_discount(order, 0.05)
```

**Expected Outcomes:** 15-25% increase in profit margins, optimized inventory turnover
**Challenges:** Price volatility may confuse customers, requires sophisticated monitoring

---

### **Shopping Cart Abandonment Recovery**
**Business Context:** E-commerce platform wants to automatically engage customers who abandon their shopping carts.

**Business Logic:**
- If cart_value > $50 AND abandoned_time > 1 hour, send discount email
- If cart contains sale items AND abandoned_time > 30 minutes, send urgency notification
- If customer has abandoned 3+ carts in 30 days, offer personalized assistance
- Premium customers get immediate phone call for high-value abandonment

**Implementation Example:**
```
WORKFLOW: Cart_Abandonment_Recovery
TRIGGER: cart.last_activity > 60 minutes AND cart.status == "ACTIVE"

IF cart.total_value >= 50
THEN schedule_email("discount_offer", delay=1_hour)

IF cart.contains_sale_items() AND cart.abandoned_time >= 30
THEN send_notification("limited_time_offer")
```

**Expected Outcomes:** 10-15% cart recovery rate improvement
**Challenges:** Avoiding spam perception, timing optimization

---

### **Inventory Management Automation**
**Business Context:** Multi-location retailer needs automated reordering and stock allocation.

**Business Logic:**
- Reorder when: current_stock <= (daily_sales_avg × lead_time_days × 1.5)
- Seasonal adjustments: increase reorder point by 40% during peak seasons
- Allocate new inventory based on: 60% historical performance, 40% current demand
- Fast-moving items get priority allocation to high-traffic stores

**Implementation Example:**
```
RULE: Auto_Reorder_Point
reorder_threshold = (average_daily_sales * lead_time_days * safety_factor)

IF current_inventory <= reorder_threshold
   AND supplier.status == "ACTIVE"
   AND product.discontinuation_date > current_date + 90_days
THEN create_purchase_order(calculate_order_quantity())
```

**Expected Outcomes:** 30% reduction in stockouts, 20% lower holding costs
**Challenges:** Seasonal demand prediction, supplier reliability

---

## **Financial Services**

### **Credit Scoring and Loan Approval**
**Business Context:** Bank needs automated loan decision system for personal and business loans.

**Business Logic:**
- Credit score ≥ 750: Pre-approved up to 6x monthly income
- Credit score 650-749: Manual review required, max 4x income
- Credit score < 650: Requires co-signer or collateral
- Debt-to-income ratio must be ≤ 40%
- Self-employed applicants need 2 years tax returns

**Implementation Example:**
```
DECISION_TABLE: Loan_Approval
IF credit_score >= 750 AND debt_to_income <= 0.40 AND employment_stable == true
THEN decision = "AUTO_APPROVE", max_amount = monthly_income * 6

IF credit_score BETWEEN 650 AND 749 AND debt_to_income <= 0.35
THEN decision = "MANUAL_REVIEW", max_amount = monthly_income * 4

IF applicant.employment_type == "SELF_EMPLOYED"
THEN required_documents.add("tax_returns_2_years")
```

**Expected Outcomes:** 80% faster loan processing, 15% lower default rates
**Challenges:** Regulatory compliance, bias prevention, exception handling

---

### **Fraud Detection System**
**Business Context:** Credit card company needs real-time fraud detection for transactions.

**Business Logic:**
- Flag if: transaction_amount > 3x average_monthly_spending
- Block if: multiple transactions in different countries within 2 hours
- Alert if: purchasing pattern differs significantly from historical data
- Whitelist: known merchants, frequent locations, recurring payments

**Implementation Example:**
```
RULE: Real_Time_Fraud_Detection
IF transaction.amount > customer.avg_monthly_spend * 3
   AND transaction.merchant NOT IN customer.frequent_merchants
   AND time_since_last_transaction < 10_minutes
THEN flag_for_review(transaction, "HIGH_AMOUNT_UNUSUAL_MERCHANT")

IF count_transactions_last_2_hours(customer) > 10
   AND distinct_countries(recent_transactions) > 1
THEN block_transaction(transaction, "VELOCITY_CHECK")
```

**Expected Outcomes:** 95% fraud detection accuracy, <1% false positive rate
**Challenges:** Balancing security with customer experience, evolving fraud patterns

---

### **Investment Portfolio Rebalancing**
**Business Context:** Wealth management firm needs automated portfolio rebalancing for clients.

**Business Logic:**
- Rebalance when any asset class deviates >5% from target allocation
- Conservative portfolios: max 30% equities, min 50% bonds
- Aggressive portfolios: max 90% equities, min 5% cash
- Tax-loss harvesting: sell losers in taxable accounts first
- Minimum transaction: $1,000 to avoid excessive fees

**Implementation Example:**
```
RULE: Portfolio_Rebalancing
FOR each asset_class IN portfolio
  IF abs(current_allocation - target_allocation) > 0.05
  THEN calculate_rebalancing_trades()

IF portfolio.risk_profile == "CONSERVATIVE"
   AND equity_allocation > 0.30
THEN reduce_equity_exposure(target=0.25)

IF account.type == "TAXABLE" AND rebalancing_required
THEN prioritize_tax_loss_harvesting()
```

**Expected Outcomes:** Maintains target risk levels, optimizes tax efficiency
**Challenges:** Market timing, tax implications, transaction costs

---

## **Healthcare**

### **Patient Appointment Scheduling**
**Business Context:** Hospital system needs intelligent scheduling considering doctor availability, patient preferences, and medical priorities.

**Business Logic:**
- Emergency cases: schedule within 2 hours
- Urgent cases: schedule within 24 hours  
- Routine appointments: schedule within 2 weeks
- Specialist referrals: require primary care approval
- Follow-up appointments: auto-schedule based on treatment protocol

**Implementation Example:**
```
WORKFLOW: Patient_Scheduling
IF patient.condition_severity == "EMERGENCY"
THEN schedule_immediately(find_available_doctor(specialty_required))

IF appointment.type == "FOLLOW_UP"
   AND treatment_protocol.requires_follow_up
THEN auto_schedule(days_from_now = protocol.follow_up_days)

IF referral.specialty_required NOT IN primary_doctor.specialties
THEN require_specialist_referral(referral.specialty_required)
```

**Expected Outcomes:** 90% appointment satisfaction, optimized resource utilization
**Challenges:** Doctor availability, emergency prioritization, patient preferences

---

### **Medication Interaction Checking**
**Business Context:** Pharmacy system needs real-time drug interaction and allergy checking.

**Business Logic:**
- Check all prescribed medications against patient's current prescriptions
- Flag dangerous interactions (Level 1: contraindicated, Level 2: caution)
- Verify dosage against patient weight, age, kidney/liver function
- Alert for known allergies or adverse reactions
- Require pharmacist override for Level 1 interactions

**Implementation Example:**
```
RULE: Medication_Safety_Check
FOR each new_medication IN prescription
  FOR each existing_medication IN patient.current_medications
    IF drug_interaction_database.check(new_medication, existing_medication) == "CONTRAINDICATED"
    THEN block_prescription(reason="DANGEROUS_INTERACTION", requires_override=true)

IF new_medication IN patient.known_allergies
THEN alert_pharmacist("ALLERGY_ALERT", severity="HIGH")
```

**Expected Outcomes:** 99% drug interaction detection, reduced adverse events
**Challenges:** Database accuracy, override protocols, emergency situations

---

### **Clinical Decision Support**
**Business Context:** Electronic Health Record system provides treatment recommendations based on symptoms and medical history.

**Business Logic:**
- Diabetic patients with HbA1c >7%: recommend medication adjustment
- Hypertension + diabetes: prescribe ACE inhibitor as first-line treatment
- Chest pain + risk factors: order immediate ECG and cardiac enzymes
- Preventive care reminders based on age, gender, and risk factors

**Implementation Example:**
```
RULE: Clinical_Decision_Support
IF patient.diabetes == true 
   AND latest_hba1c > 7.0
   AND last_medication_change > 90_days
THEN recommend("Consider medication adjustment", evidence_level="A")

IF patient.symptoms.contains("chest_pain")
   AND cardiac_risk_score > 0.6
THEN urgent_order(["ECG", "Troponin", "CK-MB"], priority="STAT")
```

**Expected Outcomes:** Improved care quality, reduced medical errors
**Challenges:** Alert fatigue, physician acceptance, liability concerns

---

## **Human Resources**

### **Employee Performance Evaluation**
**Business Context:** Company needs automated performance review process with fair evaluation criteria.

**Business Logic:**
- Performance rating = 40% goals achievement + 30% peer feedback + 20% manager rating + 10% self-assessment
- Ratings below 2.5/5.0 trigger performance improvement plan
- Top 10% performers eligible for fast-track promotion
- 360-degree feedback required for management positions
- Calibration meetings required when ratings differ significantly between reviewers

**Implementation Example:**
```
CALCULATION: Performance_Score
performance_score = (goals_achievement * 0.4) + 
                   (peer_feedback_avg * 0.3) + 
                   (manager_rating * 0.2) + 
                   (self_assessment * 0.1)

IF performance_score < 2.5
THEN trigger_pip(employee, duration=90_days)

IF employee.role.level >= "MANAGER"
THEN require_360_feedback(minimum_reviewers=5)
```

**Expected Outcomes:** Fair performance evaluation, reduced bias, clear improvement paths
**Challenges:** Reviewer bias, goal setting consistency, employee acceptance

---

### **Automated Recruitment Screening**
**Business Context:** HR department needs to screen hundreds of applications efficiently while maintaining fairness.

**Business Logic:**
- Required qualifications: education, experience, certifications
- Preferred qualifications: additional skills, culture fit indicators
- Diversity considerations: ensure balanced candidate pool
- Red flags: employment gaps >2 years, frequent job changes
- Auto-advance high-scoring candidates to next round

**Implementation Example:**
```
SCORING: Candidate_Evaluation
base_score = 0

IF candidate.education.meets_requirements()
THEN base_score += 25

IF candidate.experience_years >= job.min_experience
THEN base_score += 30

FOR each skill IN job.required_skills
  IF skill IN candidate.skills
  THEN base_score += 10

IF base_score >= 70 AND no_red_flags(candidate)
THEN advance_to_next_round(candidate)
```

**Expected Outcomes:** 60% faster screening, improved candidate quality
**Challenges:** Bias prevention, skill assessment accuracy, legal compliance

---

### **Leave Management System**
**Business Context:** Multi-location company needs automated leave approval and coverage management.

**Business Logic:**
- Vacation requests require 2 weeks advance notice
- Sick leave: immediate approval up to 5 days, medical certificate for longer
- Maximum 30% of team can be on leave simultaneously
- Critical periods (end of quarter): restrict non-essential leave
- Automatic coverage assignment based on skills and availability

**Implementation Example:**
```
RULE: Leave_Approval
IF leave_request.type == "VACATION"
   AND advance_notice >= 14_days
   AND team_coverage_percentage < 0.3
   AND NOT critical_period(leave_request.dates)
THEN auto_approve(leave_request)

IF leave_request.type == "SICK"
   AND duration <= 5_days
THEN auto_approve(leave_request), notify_manager()

ELSE require_manager_approval(leave_request)
```

**Expected Outcomes:** Improved coverage, faster approvals, better planning
**Challenges:** Fair allocation, emergency coverage, seasonal demand

---

## **Manufacturing**

### **Predictive Maintenance Scheduling**
**Business Context:** Manufacturing plant needs to prevent equipment failures while minimizing maintenance costs.

**Business Logic:**
- Schedule maintenance when: equipment_health_score < 70%
- Critical equipment: check daily, non-critical: check weekly
- Maintenance priority: safety risk > production impact > cost
- Parts ordering: automatically order when lead time + safety stock reached
- Maintenance windows: schedule during planned downtime when possible

**Implementation Example:**
```
RULE: Predictive_Maintenance
IF equipment.health_score < 70
   OR operating_hours > maintenance_threshold
   OR vibration_levels > normal_range * 1.5
THEN schedule_maintenance(equipment, priority=calculate_priority())

IF equipment.criticality == "HIGH"
   AND next_maintenance_due <= 7_days
THEN order_spare_parts(equipment.maintenance_kit)
```

**Expected Outcomes:** 25% reduction in unplanned downtime, 20% lower maintenance costs
**Challenges:** Sensor accuracy, maintenance scheduling conflicts, parts availability

---

### **Quality Control Automation**
**Business Context:** Production line needs automated quality inspection and defect management.

**Business Logic:**
- Inspect every 10th product for routine quality checks
- 100% inspection for critical safety components
- Defect rate >2%: stop production and investigate
- Three consecutive defects: automatic line shutdown
- Quality trends: alert when degradation pattern detected

**Implementation Example:**
```
RULE: Quality_Control
IF product.safety_critical == true
THEN perform_full_inspection(product)

ELSE IF production_count % 10 == 0
THEN perform_sample_inspection(product)

IF current_defect_rate > 0.02
   OR consecutive_defects >= 3
THEN stop_production_line(), notify_quality_manager()

IF quality_trend_analysis() == "DEGRADING"
THEN alert_production_supervisor("Quality trend declining")
```

**Expected Outcomes:** 99.5% quality compliance, reduced waste
**Challenges:** Inspection speed vs. accuracy, false positives, cost balance

---

### **Supply Chain Optimization**
**Business Context:** Manufacturer needs to optimize supplier selection and inventory across multiple facilities.

**Business Logic:**
- Primary supplier: best price + quality score >90%
- Backup supplier required for critical components
- Supplier performance: delivery time, quality, price stability
- Multi-sourcing: no single supplier >60% of critical components
- Geographic diversification: avoid concentration risk

**Implementation Example:**
```
RULE: Supplier_Selection
FOR each component IN critical_components
  primary_supplier = SELECT supplier 
                    WHERE quality_score >= 90
                    ORDER BY (price * 0.6 + delivery_time * 0.4)
                    LIMIT 1

  backup_supplier = SELECT supplier 
                   WHERE supplier != primary_supplier 
                   AND quality_score >= 85
                   ORDER BY diversification_score DESC
                   LIMIT 1

IF supplier.market_share(component) > 0.6
THEN find_alternative_supplier(component, target_share=0.4)
```

**Expected Outcomes:** 15% cost reduction, improved supply resilience
**Challenges:** Supplier relationship management, quality consistency, cost optimization

---

## **Transportation & Logistics**

### **Dynamic Route Optimization**
**Business Context:** Delivery company needs real-time route optimization considering traffic, vehicle capacity, and customer preferences.

**Business Logic:**
- Optimize for: minimum total distance + delivery time windows + fuel costs
- Vehicle capacity constraints: weight, volume, special handling requirements
- Driver constraints: maximum hours, skill requirements, geographic knowledge
- Customer priorities: premium customers get preferred time slots
- Real-time adjustments: traffic, weather, vehicle breakdowns

**Implementation Example:**
```
ALGORITHM: Route_Optimization
FOR each delivery_route
  WHILE unassigned_deliveries.exists()
    next_stop = SELECT delivery 
                WHERE fits_vehicle_capacity(current_vehicle)
                AND within_time_window(delivery.preferred_time)
                ORDER BY (distance_factor * 0.4 + 
                         priority_factor * 0.3 + 
                         time_window_factor * 0.3)
                LIMIT 1
    
    IF traffic_delay > 15_minutes
    THEN recalculate_route(remaining_deliveries)
```

**Expected Outcomes:** 20% reduction in fuel costs, 95% on-time delivery
**Challenges:** Real-time data accuracy, optimization complexity, driver acceptance

---

### **Fleet Maintenance Management**
**Business Context:** Transportation company manages maintenance for hundreds of vehicles across multiple locations.

**Business Logic:**
- Preventive maintenance: every 10,000 miles or 6 months
- Vehicle age considerations: older vehicles need more frequent inspections
- Route-based adjustments: highway vs. city driving affects maintenance schedules
- Regulatory compliance: DOT inspections, emission tests
- Cost optimization: batch maintenance at preferred service centers

**Implementation Example:**
```
RULE: Fleet_Maintenance_Scheduling
IF vehicle.mileage >= last_maintenance_mileage + 10000
   OR days_since_maintenance >= 180
   OR inspection_due_date <= current_date + 30
THEN schedule_maintenance(vehicle, calculate_service_center())

IF vehicle.age > 5_years
THEN increase_inspection_frequency(vehicle, factor=1.5)

IF vehicle.route_type == "CITY_DELIVERY"
THEN adjust_maintenance_schedule(factor=1.2)  // More frequent due to stop-and-go
```

**Expected Outcomes:** 30% reduction in breakdowns, improved regulatory compliance
**Challenges:** Scheduling coordination, cost management, vehicle availability

---

## **Insurance**

### **Claims Processing Automation**
**Business Context:** Insurance company needs automated claims assessment and approval workflow.

**Business Logic:**
- Auto-approve claims: <$5,000 AND no fraud indicators AND policy in good standing
- Require adjuster review: >$5,000 OR fraud score >0.3 OR multiple recent claims
- Fast-track processing: policy holders >5 years AND excellent payment history
- Fraud detection: unusual claim patterns, inconsistent information
- Settlement calculation: based on policy terms, deductibles, depreciation

**Implementation Example:**
```
WORKFLOW: Claims_Processing
IF claim.amount <= 5000 
   AND fraud_score(claim) < 0.1 
   AND policy.status == "ACTIVE"
   AND policy.payment_status == "CURRENT"
THEN auto_approve_claim(claim), process_payment()

ELSE assign_to_adjuster(claim, priority=calculate_priority())

IF claim.amount > 50000 OR claim.type == "TOTAL_LOSS"
THEN require_senior_adjuster_approval(claim)
```

**Expected Outcomes:** 70% faster claim processing, reduced fraud losses
**Challenges:** Fraud detection accuracy, customer satisfaction, regulatory compliance

---

### **Underwriting Risk Assessment**
**Business Context:** Insurance company needs automated risk assessment for policy applications.

**Business Logic:**
- Life insurance: age, health, lifestyle, occupation, coverage amount
- Auto insurance: driving record, vehicle type, location, annual mileage
- Home insurance: property value, location, construction type, security features
- Risk scoring: combine multiple factors with weighted importance
- Pricing: base rate × risk multiplier × market adjustments

**Implementation Example:**
```
CALCULATION: Risk_Assessment
base_risk_score = 1.0

// Age factor for life insurance
IF applicant.age > 65
THEN base_risk_score *= 1.5

// Driving record for auto insurance  
violations_last_3_years = count_violations(applicant, 3_years)
IF violations_last_3_years > 2
THEN base_risk_score *= (1.0 + violations_last_3_years * 0.15)

// Location risk for home insurance
IF property.flood_zone == "HIGH_RISK"
THEN base_risk_score *= 1.8

final_premium = base_premium * base_risk_score * market_adjustment
```

**Expected Outcomes:** More accurate pricing, improved profitability
**Challenges:** Data accuracy, regulatory requirements, competitive pricing

---

## **Telecommunications**

### **Network Traffic Management**
**Business Context:** Telecom provider needs dynamic bandwidth allocation and quality of service management.

**Business Logic:**
- Priority levels: Emergency > Business > Premium > Standard
- Traffic shaping: throttle during peak hours if network congestion >80%
- QoS guarantees: minimum bandwidth for premium customers
- Fair usage: soft caps with speed reduction after limits
- Network optimization: route traffic through least congested paths

**Implementation Example:**
```
RULE: Traffic_Management
IF network_congestion > 0.8 AND current_time IN peak_hours
THEN apply_traffic_shaping(priority_levels)

FOR each customer_connection
  IF customer.plan == "PREMIUM" 
  THEN guarantee_bandwidth(customer, minimum=customer.plan.guaranteed_speed)
  
  IF customer.monthly_usage > customer.plan.soft_cap
  THEN reduce_speed(customer, reduction=0.5)
  
IF connection.service_type == "EMERGENCY"
THEN prioritize_traffic(connection, priority=1)
```

**Expected Outcomes:** Improved network performance, customer satisfaction
**Challenges:** Fair allocation, peak demand management, emergency prioritization

---

### **Customer Service Automation**
**Business Context:** Telecom company needs intelligent call routing and issue resolution.

**Business Logic:**
- Route calls based on: issue type, customer tier, agent skills, wait times
- Escalation triggers: call duration >20 minutes, customer satisfaction <3/5
- Self-service options: bill inquiry, service changes, troubleshooting
- VIP treatment: premium customers get priority queue
- Knowledge base: suggest solutions based on problem symptoms

**Implementation Example:**
```
WORKFLOW: Call_Routing
IF customer.tier == "VIP" OR issue.severity == "SERVICE_OUTAGE"
THEN route_to_priority_queue()

ELSE IF issue.type == "TECHNICAL_SUPPORT"
THEN route_to_agent(skill="TECHNICAL", wait_time=calculate_wait_time())

IF call_duration > 20_minutes OR customer_satisfaction < 3
THEN escalate_to_supervisor(call, reason="PERFORMANCE_THRESHOLD")

IF issue.type IN automated_resolution_types
THEN offer_self_service_option(customer, issue.type)
```

**Expected Outcomes:** 40% reduction in call center costs, improved resolution times
**Challenges:** Agent skill matching, escalation management, customer preferences

