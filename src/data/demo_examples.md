# Demo Examples — Using Our Own Data

> **Important:** All examples use fictional product names from our mock database. No Vertiv references.

---

## Product Catalog Overview

### Categories
| Category | Color | Icon | Products |
|----------|-------|------|----------|
| Cooling Solutions | Pink (#F472B6) | ❄️ | AeroCool, FrostFlow, ChillZone, ThermoMax |
| Power Protection | Indigo (#6366F1) | ⚡ | VoltGuard, PowerShield |
| Monitoring & Control | Teal (#2DD4BF) | 📊 | InfraWatch, TempGuard |
| Power Distribution | Amber (#FBBF24) | 🔌 | PowerStrip, SmartStrip, BusBar |

### Featured Products
| Code | Name | Category | Price | Use Case |
|------|------|----------|-------|----------|
| CS-LC-1000 | AeroCool Liquid C1000 | Cooling | $4,500 | 1000 sq ft data centers |
| CS-HX-3000 | ThermoMax HX3000 | Cooling | $12,500 | Large data centers |
| PW-UPS-3000 | VoltGuard UPS 3000VA | Power | $1,200 | Mid-size server rooms |
| PW-UPS-10000 | PowerShield Rack 10kVA | Power | $5,800 | Enterprise racks |
| MN-IC-PRO | InfraWatch Pro | Monitoring | $1,200 | Professional monitoring |
| PD-RU-42 | PowerStrip Rack 42U | Distribution | $650 | Rack power distribution |

### Pre-built Bundles
| Bundle | Products | Price | Savings |
|--------|----------|-------|---------|
| Edge Computing Starter | CS-AC-500 + PW-UPS-1500 + PD-SMART-8 + MN-IC-BASIC | $3,880 | 8.3% |
| Small Data Center Package | CS-LC-1000 + PW-UPS-3000 + PD-RU-42 + MN-IC-PRO | $6,550 | 12.1% |
| Medium Data Center Solution | CS-CR-2000 + PW-UPS-6000 + PD-VERT-48 + MN-TEMP-ADV | $12,900 | 9.8% |
| Enterprise Data Center Suite | CS-HX-3000 + PW-UPS-10000 + PD-BUS-MAIN + MN-IC-ENT | $37,800 | 9.6% |

---

## Demo Scenarios

### Scenario 1: Small Edge Location
**User Query:** "I need to set up a small server room at our remote office, about 150 square feet"

**Expected Agent Behavior:**
1. Parse: 150 sq ft = small edge location
2. Recommend: Edge Computing Starter bundle
3. Products to show:
   - ChillZone AC500 (compact AC)
   - VoltGuard UPS 1500VA
   - SmartStrip 8-Outlet
   - InfraWatch Basic

**Conversation Flow:**
```
User: "I need to set up a small server room at our remote office, about 150 square feet"

AI: "Perfect! For a 150 sq ft edge location, I'd recommend our Edge Computing Starter 
     package. It includes everything you need for reliable operations."

AI: [Shows Edge Computing Starter bundle - $3,880 with 8.3% savings]

User: "What's included?"

AI: "The bundle includes:
     • ChillZone AC500 - Compact air conditioning ($2,800)
     • VoltGuard UPS 1500VA - Compact UPS ($450)
     • SmartStrip 8-Outlet - Smart PDU ($280)
     • InfraWatch Basic - Temperature monitoring ($350)"

User: "Show me the cooling options"

AI: [Shows cooling category with ChillZone AC500 highlighted]
```

---

### Scenario 2: Data Center Expansion
**User Query:** "We're expanding our data center to 1000 sq ft and need cooling and power"

**Expected Agent Behavior:**
1. Parse: 1000 sq ft = small data center
2. Identify needs: Cooling + Power + Monitoring + Distribution
3. Recommend: Small Data Center Package
4. Show complementary products

**Conversation Flow:**
```
User: "We're expanding our data center to 1000 sq ft and need cooling and power"

AI: "Great! For a 1000 sq ft data center, I recommend liquid cooling and redundant 
     power. Let me show you our Small Data Center Package."

AI: [Shows Small Data Center Package - $6,550 with 12.1% savings]

AI: "This includes:
     • AeroCool Liquid C1000 - Liquid cooling ($4,500)
     • VoltGuard UPS 3000VA - Tower UPS ($1,200)
     • PowerStrip Rack 42U - Rack PDU ($650)
     • InfraWatch Pro - Professional monitoring ($1,200)"

User: "What's the cooling capacity?"

AI: "The AeroCool Liquid C1000 provides 1000W of cooling capacity, perfect for your 
     1000 sq ft space. It features intelligent temperature control and redundant pumps."

User: "Add this to my solution"

AI: [Adds bundle to solution, shows category coverage: cooling, power, distribution, monitoring]
```

---

### Scenario 3: High-Density Cooling
**User Query:** "We have high-density racks generating a lot of heat. What cooling do you recommend?"

**Expected Agent Behavior:**
1. Parse: High-density = need targeted/in-row cooling
2. Recommend: FrostFlow CR2000 (in-row cooling)
3. Suggest: Monitoring with TempGuard Advanced

**Conversation Flow:**
```
User: "We have high-density racks generating a lot of heat. What cooling do you recommend?"

AI: "For high-density racks, I recommend in-row cooling that targets heat directly. 
     The FrostFlow CR2000 is perfect for this scenario."

AI: [Shows FrostFlow CR2000 - $6,200]

AI: "Key features:
     • 2000W capacity
     • In-row placement next to hot racks
     • Variable speed EC motors
     • 300mm width fits standard aisle"

User: "Do I need monitoring too?"

AI: "Absolutely! For high-density environments, thermal monitoring is critical. 
     I recommend TempGuard Advanced with thermal imaging to prevent hotspots."

AI: [Shows TempGuard Advanced - $2,800]

User: "Show me both"

AI: [Shows Advanced Cooling & Monitoring bundle - $9,500 with 5.9% savings]
```

---

### Scenario 4: Category Browsing
**User Query:** "Show me all your power protection options"

**Expected Agent Behavior:**
1. Filter to Power category
2. Show products from $450 to $5,800
3. Allow comparison

**Conversation Flow:**
```
User: "Show me all your power protection options"

AI: [Shows Power Protection category with 4 products]

AI: "We have 4 UPS systems for different needs:

     Entry Level:
     • VoltGuard UPS 1500VA - $450 (1500VA, 15 min runtime)
     
     Mid-Range:
     • VoltGuard UPS 3000VA - $1,200 (3000VA, 12 min runtime)
     • PowerShield Rack 6kVA - $3,200 (6000VA, rack-mount)
     
     Enterprise:
     • PowerShield Rack 10kVA - $5,800 (10kVA, scalable runtime)"

User: "Compare the 3000VA and 6000VA models"

AI: [Shows comparison side-by-side]
```

---

### Scenario 5: Building a Custom Solution
**User Query:** "I need liquid cooling for 1000 sq ft"

**Agent builds solution step by step:**

```
User: "I need liquid cooling for 1000 sq ft"

AI: [Searches products, finds CS-LC-1000]

AI: "Perfect! The AeroCool Liquid C1000 is designed exactly for 1000 sq ft data centers. 
     It provides 1000W cooling capacity with intelligent controls."

AI: [Shows CS-LC-1000 - $4,500 - IN STOCK]

User: "Add to solution"

AI: [Adds to solution]
AI: "Your solution now covers cooling. To complete your infrastructure, 
     you may also need power protection and monitoring."

AI: [Shows complementary suggestions: VoltGuard UPS 3000VA, InfraWatch Pro]

User: "Add the UPS too"

AI: [Adds PW-UPS-3000 to solution]
AI: "Solution updated! Categories covered: cooling, power. 
     Still recommended: monitoring, distribution"
```

---

## API Test Examples

### Search Products
```bash
curl "http://localhost:8000/api/v1/products/search?q=liquid+cooling&limit=5"
```

Expected: Returns AeroCool Liquid C1000, FrostFlow CR2000, ThermoMax HX3000

### Get Category Products
```bash
curl "http://localhost:8000/api/v1/categories/power/products?in_stock_only=true"
```

Expected: Returns 4 power products (VoltGuard 1500VA, 3000VA, PowerShield 6kVA, 10kVA)

### Get Bundle
```bash
curl "http://localhost:8000/api/v1/bundles/bundle-dc-small"
```

Expected: Returns Small Data Center Package with full product details

### AI Recommendations
```bash
curl "http://localhost:8000/api/v1/ai/recommend?use_case=cooling+for+1000+sq+ft&space_size=1000"
```

Expected: Returns AeroCool Liquid C1000, suggests Small Data Center Package

---

## Design Validation

### Arc-Inspired Elements in Demo
1. **Gradient background** behind chat panel
2. **Category pills** with category colors (pink for cooling, etc.)
3. **Floating product cards** with rounded corners
4. **Soft shadows** on cards
5. **Playful icons** (❄️ ⚡ 📊 🔌)

### Colors Used
| Element | Color | Usage |
|---------|-------|-------|
| Cooling | #F472B6 (Pink) | Category pills, badges |
| Power | #6366F1 (Indigo) | Category pills, badges |
| Monitoring | #2DD4BF (Teal) | Category pills, badges |
| Distribution | #FBBF24 (Amber) | Category pills, badges |
| Background | #FAFAFA (Off-white) | Page background |
| Surface | #FFFFFF (White) | Cards |

---

## No Vertiv References Checklist

- [x] Product names: AeroCool, FrostFlow, ChillZone, ThermoMax (fictional)
- [x] UPS names: VoltGuard, PowerShield (fictional)
- [x] Monitoring: InfraWatch, TempGuard (fictional)
- [x] Distribution: PowerStrip, SmartStrip, BusBar (fictional)
- [x] No "Vertiv" in any text
- [x] No Vertiv product names (CoolChip, Liebert, etc.)
- [x] No Vertiv imagery

All examples use our own original mock data.
