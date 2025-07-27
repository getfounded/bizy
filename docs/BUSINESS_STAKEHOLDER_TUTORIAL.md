# Business Stakeholder Tutorial: Writing AI Business Logic in Natural Language

## Welcome! 👋

This tutorial teaches business stakeholders how to write AI coordination logic using natural language. No technical background required!

## What You'll Learn

By the end of this tutorial, you'll be able to:
- Write business rules that coordinate multiple AI systems
- Create executable specifications that stay current with implementation
- Collaborate effectively with technical teams using shared language
- Validate that AI systems behave according to business requirements

## Table of Contents

1. [Understanding BDD for Business Logic](#understanding-bdd)
2. [Basic Scenario Structure](#basic-structure)
3. [Writing Your First Scenario](#first-scenario)
4. [Common Business Patterns](#common-patterns)
5. [Advanced Scenarios](#advanced-scenarios)
6. [Validation and Testing](#validation)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Understanding BDD for Business Logic {#understanding-bdd}

### What is BDD?

**Behavior-Driven Development (BDD)** lets you write business requirements in natural language that can be automatically executed by computers. Think of it as writing instructions that both humans and machines can understand.

### Why Use BDD for AI Business Logic?

Traditional approach:
1. 📝 Business writes requirements in documents
2. 🔄 Technical team translates to code
3. ❓ Miscommunication and errors occur
4. 🐛 Problems discovered late in development

BDD approach:
1. 📝 Business writes requirements in structured natural language
2. ✅ Requirements are immediately executable
3. 🤖 AI systems follow business logic exactly as written
4. 📊 Real-time validation ensures requirements are met

### Example: Before and After

**Before (Traditional)**:
> "When a premium customer complains, escalate to their account manager and start the priority support workflow."

**After (BDD)**:
```gherkin
Scenario: Premium customer complaint escalation
  Given a customer with tier "premium"
  And the customer sentiment score is below 0.3
  When a support interaction is created
  Then escalate to account manager via MCP toolkit
  And start priority workflow via Temporal
```

The BDD version is:
- ✅ **Precise**: Defines exact conditions (sentiment < 0.3)
- ✅ **Executable**: Can be run automatically
- ✅ **Testable**: Can verify it works correctly
- ✅ **Maintainable**: Easy to update when business rules change

---

## Basic Scenario Structure {#basic-structure}

Every business scenario follows the same pattern:

```gherkin
Scenario: [Business Process Name]
  Given [Condition 1]
  And [Condition 2]
  When [Trigger Event]
  Then [Action 1]
  And [Action 2]
```

### The Three Parts

#### 1. **Given** (Conditions)
Define when the business rule should apply:
- Customer characteristics: `Given a customer with tier "premium"`
- Data conditions: `And data size is greater than 1000`
- System states: `And LangChain is available for document analysis`

#### 2. **When** (Trigger)
Describe what event starts the process:
- `When a support interaction is created`
- `When a customer uploads a document`
- `When the data pipeline is triggered`

#### 3. **Then** (Actions)
Specify what should happen:
- `Then analyze sentiment using LangChain`
- `And start escalation workflow via Temporal`
- `And notify account manager via MCP toolkit`

### AI Systems Available

Our platform coordinates these AI systems:

| System | Best For | Example Actions |
|--------|----------|-----------------|
| **LangChain** | Document analysis, content processing | analyze document, extract information |
| **Semantic Kernel** | Complex workflows, agent coordination | coordinate agents, run complex process |
| **MCP Toolkit** | External system integration | notify manager, update CRM |
| **Temporal** | Reliable workflows, process automation | start workflow, manage process |
| **FastMCP** | High-volume data processing | batch process, transform data |
| **Zep** | Memory and knowledge management | store context, remember information |

---

## Writing Your First Scenario {#first-scenario}

Let's create a scenario step-by-step for customer service automation.

### Step 1: Identify the Business Process

**Question**: What business process are you automating?
**Answer**: "Handle customer complaints from premium customers"

### Step 2: Define Conditions (Given)

**Question**: When should this process trigger?
**Conditions**:
- Customer must be premium tier
- Customer must be unsatisfied (negative sentiment)
- Complaint must be about billing

```gherkin
Given a customer with tier "premium"
And the customer sentiment score is below 0.4
And the complaint category is "billing"
```

### Step 3: Define Trigger (When)

**Question**: What event starts this process?
**Answer**: When a support ticket is created

```gherkin
When a support ticket is submitted
```

### Step 4: Define Actions (Then)

**Question**: What should happen?
**Actions**:
1. Analyze the complaint details
2. Escalate to billing specialist
3. Start priority resolution workflow
4. Remember this interaction

```gherkin
Then analyze complaint details using LangChain
And escalate to billing specialist via MCP toolkit
And start priority resolution workflow via Temporal
And store interaction context in Zep memory
```

### Step 5: Complete Scenario

```gherkin
Scenario: Premium customer billing complaint handling
  Given a customer with tier "premium"
  And the customer sentiment score is below 0.4
  And the complaint category is "billing"
  When a support ticket is submitted
  Then analyze complaint details using LangChain
  And escalate to billing specialist via MCP toolkit
  And start priority resolution workflow via Temporal
  And store interaction context in Zep memory
```

### Step 6: Validate Your Scenario

Ask yourself:
- ✅ Are the conditions specific enough?
- ✅ Is the trigger event clear?
- ✅ Do the actions solve the business problem?
- ✅ Would this scenario work for similar situations?

---

## Common Business Patterns {#common-patterns}

Here are proven patterns for common business scenarios:

### Pattern 1: Customer Escalation

```gherkin
Scenario: [Customer Type] [Issue Type] escalation
  Given a customer with [characteristic] "[value]"
  And the [metric] is [condition] [threshold]
  When a [interaction type] is created
  Then [analysis action] using [AI system]
  And [escalation action] via [system]
  And [workflow action] via [system]
```

**Example**:
```gherkin
Scenario: Enterprise customer service escalation
  Given a customer with tier "enterprise"
  And the sentiment score is below 0.2
  When a support interaction is created
  Then analyze urgency using LangChain
  And notify account manager via MCP toolkit
  And start escalation workflow via Temporal
```

### Pattern 2: Document Processing

```gherkin
Scenario: [Document Type] processing workflow
  Given [document characteristics]
  And [system availability]
  When a document is uploaded
  Then extract [information] using LangChain
  And [processing action] via [system]
  And [storage action] via [system]
```

**Example**:
```gherkin
Scenario: Legal contract processing workflow
  Given a legal document is uploaded
  And LangChain is available for document analysis
  When a customer uploads a document
  Then extract contract terms using LangChain
  And start legal review workflow via Temporal
  And store contract data in Zep memory
```

### Pattern 3: Data Pipeline

```gherkin
Scenario: [Data Type] processing pipeline
  Given data size is [condition] [threshold]
  And [processing requirements]
  When the data pipeline is triggered
  Then [processing action] via [system]
  And [transformation action] via [system]
  And [storage action] via [system]
```

**Example**:
```gherkin
Scenario: Large dataset processing pipeline
  Given data size is greater than 1000
  And processing is required
  When the data pipeline is triggered
  Then batch process data via FastMCP
  And transform results via MCP toolkit
  And store processing context in Zep memory
```

---

## Advanced Scenarios {#advanced-scenarios}

### Multiple Conditions with OR Logic

```gherkin
Scenario Outline: Customer priority handling
  Given a customer with tier "<tier>"
  And the account value is above <min_value>
  When a request is submitted
  Then process with <priority> priority
  
  Examples:
    | tier       | min_value | priority |
    | premium    | 50000     | high     |
    | enterprise | 100000    | critical |
    | standard   | 200000    | high     |
```

### Error Handling and Fallbacks

```gherkin
Scenario: Document processing with fallback
  Given a document is uploaded
  And LangChain is available for analysis
  When document processing is requested
  Then extract content using LangChain
  And if extraction fails, use basic text parsing
  And store results in Zep memory
  And notify user of completion status
```

### Time-Based Conditions

```gherkin
Scenario: Weekend request handling
  Given a support request is submitted
  And the current time is weekend
  And the request priority is "urgent"
  When the request is processed
  Then queue for Monday morning review
  And send acknowledgment to customer
  And escalate if customer tier is "enterprise"
```

### Complex Business Logic

```gherkin
Scenario: Multi-factor customer routing
  Given a customer with the following attributes:
    | attribute     | value    |
    | tier         | premium  |
    | region       | US       |
    | language     | English  |
    | issue_type   | technical|
  When a support request is created
  Then route to US technical team via MCP toolkit
  And analyze technical complexity using LangChain
  And if complexity is high, escalate to senior engineer
  And track resolution time via Temporal workflow
```

---

## Validation and Testing {#validation}

### Interactive Scenario Builder

Use our interactive tool to create scenarios with guidance:

```bash
# Start the scenario builder
poetry run python -m business_logic_orchestrator.cli.scenario_builder --build

# Validate an existing scenario
poetry run python -m business_logic_orchestrator.cli.scenario_builder --validate my_scenario.feature

# Generate a template
poetry run python -m business_logic_orchestrator.cli.scenario_builder --template customer
```

### Validation Checklist

Before finalizing your scenario, check:

#### ✅ **Clarity**
- [ ] Scenario name clearly describes the business process
- [ ] Conditions are specific and measurable
- [ ] Actions have clear business value

#### ✅ **Completeness**
- [ ] All necessary conditions are included
- [ ] Actions address the business need
- [ ] Error handling is considered

#### ✅ **Correctness**
- [ ] AI systems chosen are appropriate for the tasks
- [ ] Business logic reflects actual policies
- [ ] Edge cases are handled

#### ✅ **Testability**
- [ ] Conditions can be verified
- [ ] Actions produce measurable outcomes
- [ ] Success criteria are clear

### Testing Your Scenarios

```bash
# Run all business scenarios
poetry run behave features/

# Run specific scenario types
poetry run behave features/ --tags=@customer_service

# Generate test report
poetry run behave features/ --format=json --outfile=business_test_results.json
```

---

## Best Practices {#best-practices}

### 1. **Start Simple**

❌ **Avoid**: Complex scenarios on first attempt
```gherkin
Scenario: Complex multi-system enterprise workflow with seventeen conditions
  Given customer tier is "enterprise" or "premium"
  And account value is above 100000 but below 1000000
  And sentiment score is below 0.3 but above 0.1
  And region is "US" or "Canada" or "UK"
  And time is business hours unless urgent
  # ... 12 more conditions
```

✅ **Better**: Start with essential conditions
```gherkin
Scenario: Enterprise customer escalation
  Given a customer with tier "enterprise"
  And the sentiment score is below 0.3
  When a support interaction is created
  Then escalate to account manager via MCP toolkit
```

### 2. **Use Descriptive Names**

❌ **Avoid**: Generic names
```gherkin
Scenario: Customer process
Scenario: Data handling
Scenario: Document stuff
```

✅ **Better**: Specific business processes
```gherkin
Scenario: Premium customer complaint escalation
Scenario: Large dataset quality validation
Scenario: Legal contract term extraction
```

### 3. **Make Conditions Measurable**

❌ **Avoid**: Vague conditions
```gherkin
Given an unhappy customer
And a big data file
```

✅ **Better**: Specific thresholds
```gherkin
Given the customer sentiment score is below 0.3
And data size is greater than 1000 records
```

### 4. **Group Related Scenarios**

Organize scenarios by business domain:

```
features/
├── customer_service.feature
├── document_processing.feature
├── data_pipeline.feature
└── financial_workflows.feature
```

### 5. **Use Business Language**

❌ **Avoid**: Technical jargon
```gherkin
Then execute POST request to CRM API endpoint
And invoke sentiment analysis ML model
```

✅ **Better**: Business actions
```gherkin
Then update customer record via MCP toolkit
And analyze customer sentiment using LangChain
```

### 6. **Keep Actions Atomic**

❌ **Avoid**: Complex combined actions
```gherkin
Then analyze sentiment and extract entities and update CRM and notify manager
```

✅ **Better**: Separate, clear actions
```gherkin
Then analyze customer sentiment using LangChain
And extract key information using LangChain
And update customer record via MCP toolkit
And notify account manager via MCP toolkit
```

---

## Troubleshooting {#troubleshooting}

### Common Issues and Solutions

#### Issue: "My scenario doesn't trigger"

**Problem**: Conditions are too restrictive
```gherkin
Given a customer with tier "premium"
And the sentiment score is exactly 0.25
And the account value is exactly 50000
```

**Solution**: Use ranges instead of exact values
```gherkin
Given a customer with tier "premium"
And the sentiment score is below 0.3
And the account value is above 45000
```

#### Issue: "Actions don't happen in the right order"

**Problem**: Order dependency not clear
```gherkin
Then notify manager via MCP toolkit
And analyze sentiment using LangChain
Then start workflow via Temporal
```

**Solution**: Organize actions logically
```gherkin
Then analyze sentiment using LangChain
And start workflow via Temporal
And notify manager via MCP toolkit
```

#### Issue: "Scenario is too complex"

**Problem**: Too many conditions and actions
```gherkin
Scenario: Everything customer process
  Given [15 different conditions]
  When [3 different triggers]
  Then [20 different actions]
```

**Solution**: Split into multiple focused scenarios
```gherkin
Scenario: Premium customer initial analysis
  Given a customer with tier "premium"
  When a support interaction is created
  Then analyze sentiment using LangChain

Scenario: High-priority escalation workflow
  Given sentiment analysis shows negative feedback
  And customer tier is "premium"
  When analysis is complete
  Then start escalation workflow via Temporal
```

#### Issue: "AI system isn't available"

**Problem**: Referencing unavailable system
```gherkin
Then process using CustomAI system
```

**Solution**: Use available AI systems
```gherkin
Then analyze content using LangChain
# or
Then coordinate processing via Semantic Kernel
# or
Then batch process via FastMCP
```

### Getting Help

#### 1. **Use the Interactive Builder**
```bash
poetry run python -m business_logic_orchestrator.cli.scenario_builder --build
```

#### 2. **Validate Your Scenarios**
```bash
poetry run python -m business_logic_orchestrator.cli.scenario_builder --validate my_scenario.feature
```

#### 3. **Start with Templates**
```bash
# Customer service template
poetry run python -m business_logic_orchestrator.cli.scenario_builder --template customer

# Document processing template
poetry run python -m business_logic_orchestrator.cli.scenario_builder --template document

# Data pipeline template
poetry run python -m business_logic_orchestrator.cli.scenario_builder --template data
```

#### 4. **Review Examples**
Look at the `templates/` directory for working examples of common business scenarios.

#### 5. **Test Early and Often**
```bash
# Test individual scenarios
poetry run behave features/my_scenario.feature

# Test all scenarios
poetry run behave features/
```

---

## Next Steps

Congratulations! You now know how to write AI business logic in natural language. Here's what to do next:

### 1. **Practice with Templates**
- Start with our provided templates
- Customize them for your business needs
- Test them to see how they work

### 2. **Create Your First Scenario**
- Identify a simple business process to automate
- Use the interactive builder for guidance
- Start with 2-3 conditions and 2-3 actions

### 3. **Collaborate with Your Technical Team**
- Share your scenarios for technical review
- Work together to refine the business logic
- Use scenarios as living documentation

### 4. **Iterate and Improve**
- Test scenarios with real data
- Refine conditions based on results
- Add new scenarios as business needs evolve

### 5. **Share Your Success**
- Document business value achieved
- Share best practices with other teams
- Contribute new templates for common patterns

---

## Resources

- **Templates Directory**: `templates/` - Ready-to-use scenario templates
- **Interactive Builder**: `poetry run python -m business_logic_orchestrator.cli.scenario_builder --build`
- **Validation Tool**: `poetry run python -m business_logic_orchestrator.cli.scenario_builder --validate`
- **Examples Directory**: `features/` - Working examples of BDD scenarios
- **Demo Script**: `poetry run python demo_bdd_integration.py`

Remember: The goal is to bridge the gap between business requirements and AI implementation. Your natural language scenarios become the executable specifications that ensure AI systems behave exactly as your business requires.

Happy scenario writing! 🚀
