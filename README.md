# Warehouse and RMA Tracking System  

## 📌 Pain Points Addressed (Updated: 2023/02/13)  

### ✅ Enhancing Operational Efficiency  
Improve the efficiency of sales teams when querying product warranty and RMA repair records.  
**Responsible:** Turbo, Tony  

### ✅ Accurate Inventory Tracking  
Enable real-time tracking of precise warehouse in/out records for Taiwan warehouse operations.  
**Responsible:** Melissa  

---

## 📦 Product Barcode Structure  

- **EAN/UAC Code**  
- **P/N (Product Number)**  
- **S/N (Serial Number)**  
- 📌 *Currently recorded information:* **P/N + S/N**  

### ➕ Additional Condition (Added: 2023/01/12)  
- Tracking inbound inventory conditions.  

---

## ⚠️ Core Issue  

❌ The lack of manufacturer warranty records and shipment date tracking results in dependence on distributors for return and exchange disputes.  

✅ The **product warranty period** should be calculated based on the **serial number's corresponding factory shipment date**.  

---

## 📅 Meeting Notes (Updated: 2023/02/06)  

### ❓ Problem  
Tracking the warranty start date for products sold to customers is difficult.  

- The **ERP system only records supplier purchase transactions** but lacks warehouse in/out records.  
- When **backtracking via serial number**, only supplier shipment data is available.  
- ❓ This raises concerns about whether the product was actually received into the warehouse.  

---

## 🏷️ Warehouse System Tracking  

A **systemized warehouse in/out/transfer record** that allows tracking via serial number:  

| Feature            | Description |
|--------------------|-------------|
| **Customer Information** | Who received the product? |
| **EAN/UAC Code**   | Barcode identification |
| **P/N (Product Number)** | Product model number |
| **S/N (Serial Number)** | Unique serial number |
| **Timestamp** | When the transaction occurred |
| **Sales Team Access** | Online query system |
| **Taiwan Warehouse Only** | Budget constraint (under 100,000 TWD) |

---

## 🛠️ System Specifications  

### 📊 **Information System Features**  
- ✅ **Quantity Tracking**  
- ✅ **Shipment Date Recording**  
- ✅ **Customer Name Association**  
- ✅ **Product Name & Code (EAN, SN)**  

### 🔍 **Hardware Scanning Mechanism**  
- 📡 Barcode scanning using **handheld scanners, PDAs, etc.**  

### 📤 **Data Import/Export**  
- ❌ *No direct ERP integration at this stage*  

### 🚀 **Expandability & Future Enhancements**  
- 🔹 Ability to **record product category codes** (e.g., PSU, Cooler, Bike, etc.).  
- 🔹 Potential feature to **track distributor shipments** while preventing backtracking of the original shipment date.  

---

📢 **This project is designed to improve warehouse operations, RMA tracking, and product warranty management while maintaining cost efficiency.**  
