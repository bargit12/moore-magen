import streamlit as st
from math import sqrt
from scipy.stats import norm

# Inject custom CSS for nicer UI and larger text
st.markdown(
    """
    <style>
    .big-font {font-size: 20px !important; }
    .header-font {font-size: 28px !important; font-weight: bold; }
    .subheader-font {font-size: 24px !important; font-weight: bold; }
    </style>
    """,
    unsafe_allow_html=True
)

# =============================================================================
# Global Parameters
# =============================================================================
st.markdown("<p class='header-font'>Supply Chain & Inventory Model Setup</p>", unsafe_allow_html=True)

interest_rate = st.number_input("Market Interest Rate (%)", min_value=0.0, max_value=100.0, value=5.0, step=0.1)
service_level = st.slider("Required Service Level (0-1)", min_value=0.0, max_value=1.0, value=0.95)
layout_type = st.radio("Layout Type", options=["Central and Fronts", "Main Regionals"])

if layout_type == "Main Regionals":
    st.info("Note: With 'Main Regionals', all warehouses must be of type MAIN.")

shipping_cost_rate = st.number_input("Shipping Cost Rate (per km per order unit)", min_value=0.0, value=1.0, step=0.1)

# קלט חדש: עלות ליחידה – נעביר אותה כמספר שלם
unit_cost = st.number_input("Unit Cost (per unit)", min_value=0, value=10, step=1, format="%d")

# חשב את ערך ה-Z עבור רמת השירות (באמצעות התפלגות נורמלית)
Z_value = norm.ppf(service_level)

# =============================================================================
# Market Areas Setup
# =============================================================================
st.markdown("<p class='subheader-font'>Market Areas Setup</p>", unsafe_allow_html=True)

base_market_areas = ["CAN", "CAS", "NE", "FL", "TX"]
st.write("Standard market areas:", base_market_areas)

custom_market_areas_str = st.text_input("Enter additional market areas (comma separated)", value="")
custom_market_areas = [area.strip() for area in custom_market_areas_str.split(",") if area.strip() != ""]

all_market_areas = list(dict.fromkeys(base_market_areas + custom_market_areas))
selected_market_areas = st.multiselect("Select Market Areas to use", options=all_market_areas, default=all_market_areas)

market_area_data = {}
for area in selected_market_areas:
    st.markdown(f"<p class='big-font'>Parameters for Market Area: {area}</p>", unsafe_allow_html=True)
    avg_order_size = st.number_input(f"Average Order Size for {area}", min_value=0, value=100, step=1, format="%d", key=f"{area}_order_size")
    avg_daily_demand = st.number_input(f"Average Daily Demand for {area}", min_value=0, value=50, step=1, format="%d", key=f"{area}_daily_demand")
    std_daily_demand = st.number_input(f"Standard Deviation of Daily Demand for {area}", min_value=0.0, value=10.0, key=f"{area}_std_demand")
    
    st.write(f"Enter 12-month Forecast Demand for {area} (each value as a whole number)")
    forecast_demand = []
    cols = st.columns(4)
    zero_demand_months = []
    for m in range(12):
        col = cols[m % 4]
        # Forecast demand as an integer
        value = col.number_input(f"Month {m+1}", min_value=0, value=0, step=1, format="%d", key=f"{area}_forecast_{m}")
        if value == 0:
            zero_demand_months.append(m+1)
        forecast_demand.append(value)
    
    if zero_demand_months:
        st.warning(f"In market area {area}, forecast demand for months {zero_demand_months} is 0. Please verify if this is intentional.")
    
    if len(forecast_demand) != 12:
        st.error(f"Forecast demand for {area} must have exactly 12 values.")
    
    market_area_data[area] = {
        "avg_order_size": avg_order_size,
        "avg_daily_demand": avg_daily_demand,
        "std_daily_demand": std_daily_demand,
        "forecast_demand": forecast_demand,
    }

# =============================================================================
# Warehouse Setup
# =============================================================================
st.markdown("<p class='subheader-font'>Warehouse Setup</p>", unsafe_allow_html=True)

base_warehouse_locations = ["CAN", "CAS", "NE", "FL", "TX"]
st.write("Standard warehouse locations:", base_warehouse_locations)

custom_warehouse_locations_str = st.text_input("Enter additional warehouse locations (comma separated)", value="")
custom_warehouse_locations = [loc.strip() for loc in custom_warehouse_locations_str.split(",") if loc.strip() != ""]
all_warehouse_locations = list(dict.fromkeys(base_warehouse_locations + custom_warehouse_locations))

num_warehouses = st.number_input("Number of Warehouses", min_value=1, value=1, step=1)

warehouse_data = []
for i in range(int(num_warehouses)):
    st.markdown(f"<p class='big-font'>Warehouse {i+1}</p>", unsafe_allow_html=True)
    location = st.selectbox(f"Select Location for Warehouse {i+1}", options=all_warehouse_locations, key=f"wh_location_{i}")
    
    if layout_type == "Main Regionals":
        wh_type = "MAIN"
        st.write("Warehouse Type: MAIN (Only MAIN allowed for Main Regionals layout)")
    else:
        wh_type = st.radio(f"Select Warehouse Type for Warehouse {i+1}", options=["MAIN", "FRONT"], key=f"wh_type_{i}")
    
    served_markets = st.multiselect(f"Select Market Areas served by Warehouse {i+1}", options=selected_market_areas, key=f"wh_markets_{i}")
    
    if location not in served_markets:
        st.error(f"Warehouse {i+1} location '{location}' must be included in its served market areas!")
    
    rent_pricing_method = st.radio(f"Select Rent Pricing Method for Warehouse {i+1} (Price per Year)", 
                                   options=["Fixed Rent Price", "Square Foot Rent Price"], key=f"rent_method_{i}")
    if rent_pricing_method == "Fixed Rent Price":
        rent_price = st.number_input(f"Enter Fixed Rent Price (per year) for Warehouse {i+1}", min_value=0.0, value=1000.0, key=f"fixed_rent_{i}")
    else:
        rent_price = st.number_input(f"Enter Rent Price per Square Foot (per year) for Warehouse {i+1}", min_value=0.0, value=10.0, key=f"sqft_rent_{i}")
    
    # קלט עבור השכר השנתי הממוצע לעובד – נעשה גם כאן כמספר שלם
    avg_employee_salary = st.number_input(f"Enter Average Annual Salary per Employee for Warehouse {i+1}", min_value=0, value=50000, step=1000, format="%d", key=f"employee_salary_{i}")
    
    wh_dict = {
        "location": location,
        "type": wh_type,
        "served_markets": served_markets,
        "rent_pricing_method": rent_pricing_method,
        "rent_price": rent_price,
        "avg_employee_salary": avg_employee_salary,
    }
    
    if wh_type == "MAIN":
        lt_shipping = st.number_input(f"Enter Lead Time (days) for shipping from Israel to Warehouse {i+1} (MAIN)", min_value=0, value=5, step=1, format="%d", key=f"lt_shipping_{i}")
        shipping_cost_40hc = st.number_input(f"Enter Shipping Cost for a 40HC container (per container) from Israel to Warehouse {i+1} (MAIN)", min_value=0, value=2000, step=1, format="%d", key=f"shipping_cost_40hc_{i}")
        wh_dict["lt_shipping"] = lt_shipping
        wh_dict["shipping_cost_40hc"] = shipping_cost_40hc
    elif wh_type == "FRONT":
        front_shipping_cost_40 = st.number_input(f"Enter Shipping Cost from MAIN warehouse to Warehouse {i+1} (FRONT) for a 40ft HC container", min_value=0, value=500, step=1, format="%d", key=f"front_shipping_cost_40_{i}")
        front_shipping_cost_53 = st.number_input(f"Enter Shipping Cost from MAIN warehouse to Warehouse {i+1} (FRONT) for a 53ft HC container", min_value=0, value=600, step=1, format="%d", key=f"front_shipping_cost_53_{i}")
        wh_dict["front_shipping_cost_40"] = front_shipping_cost_40
        wh_dict["front_shipping_cost_53"] = front_shipping_cost_53
        
        main_wh_options = []
        main_wh_mapping = {}
        for j, w in enumerate(warehouse_data):
            if w["type"] == "MAIN":
                option_str = f"Warehouse {j+1} - {w['location']}"
                main_wh_options.append(option_str)
                main_wh_mapping[option_str] = j
        if main_wh_options:
            serving_central = st.selectbox(f"Select the MAIN warehouse serving Warehouse {i+1} (FRONT)", options=main_wh_options, key=f"serving_central_{i}")
            wh_dict["serving_central"] = serving_central
            main_wh_index = main_wh_mapping.get(serving_central)
            if main_wh_index is not None:
                main_wh = warehouse_data[main_wh_index]
                common_markets = set(main_wh["served_markets"]).intersection(set(served_markets))
                if not common_markets:
                    st.error(f"Selected MAIN warehouse for Warehouse {i+1} does not serve any of its market areas!")
        else:
            st.error(f"No MAIN warehouse available to serve Warehouse {i+1} (FRONT). Please define a MAIN warehouse first.")
            wh_dict["serving_central"] = None
    warehouse_data.append(wh_dict)

# =============================================================================
# Additional Validation
# =============================================================================
st.markdown("<p class='subheader-font'>Validation</p>", unsafe_allow_html=True)

market_not_served = []
for market in selected_market_areas:
    served = any(market in wh["served_markets"] for wh in warehouse_data)
    if not served:
        market_not_served.append(market)
if market_not_served:
    st.error(f"The following market areas are not served by any warehouse: {', '.join(market_not_served)}")

# =============================================================================
# Inventory Financing Calculation
# =============================================================================
st.markdown("<p class='subheader-font'>Inventory Financing Calculation</p>", unsafe_allow_html=True)

if st.button("Calculate Inventory Financing"):
    financing_cost = 0
    total_avg_inventory = 0
    total_safety_stock = 0

    if layout_type == "Central and Fronts":
        # נאתר את המחסן המרכזי – מניחים שיש אחד שמשרת מספר אזורים (למשל, פלורידה ו-CAN)
        main_wh = next((wh for wh in warehouse_data if wh["type"] == "MAIN"), None)
        if main_wh is None:
            st.error("No MAIN warehouse found for 'Central and Fronts' layout.")
        else:
            # סכום סטיות התקן עבור כל האזורים שהמחסן המרכזי משרת
            std_sum = sum(market_area_data[area]["std_daily_demand"] for area in main_wh["served_markets"] if area in market_area_data)
            LT = main_wh.get("lt_shipping", 0)
            safety_stock_main = std_sum * sqrt(LT) * Z_value
            
            # הוספת רכיב הביטחון מהמחסנים הקדמיים: 12 * (סכום הביקוש היומי בכל מחסן FRONT)
            front_daily_demand = 0
            for wh in warehouse_data:
                if wh["type"] == "FRONT":
                    front_daily_demand += sum(market_area_data[area]["avg_daily_demand"] for area in wh["served_markets"] if area in market_area_data)
            safety_stock = safety_stock_main + 12 * front_daily_demand
            
            # Annual demand עבור כל האזורים שהמחסן המרכזי משרת
            annual_demand = 0
            for area in main_wh["served_markets"]:
                if area in market_area_data:
                    annual_demand += sum(market_area_data[area]["forecast_demand"])
            
            avg_inventory = ((annual_demand / 2) + safety_stock) / 12
            financing_cost = avg_inventory * (interest_rate / 100) * unit_cost
            
            total_avg_inventory = avg_inventory
            total_safety_stock = safety_stock

    elif layout_type == "Main Regionals":
        overall_annual_demand = 0
        overall_avg_inventory = 0
        overall_safety_stock = 0
        for wh in warehouse_data:
            if wh["type"] == "MAIN":
                std_sum = sum(market_area_data[area]["std_daily_demand"] for area in wh["served_markets"] if area in market_area_data)
                LT = wh.get("lt_shipping", 0)
                safety_stock_wh = std_sum * sqrt(LT) * Z_value
                
                annual_demand_wh = 0
                for area in wh["served_markets"]:
                    if area in market_area_data:
                        annual_demand_wh += sum(market_area_data[area]["forecast_demand"])
                
                avg_inventory_wh = ((annual_demand_wh / 2) + safety_stock_wh) / 12
                
                overall_safety_stock += safety_stock_wh
                overall_avg_inventory += avg_inventory_wh
                overall_annual_demand += annual_demand_wh
        total_avg_inventory = overall_avg_inventory
        total_safety_stock = overall_safety_stock
        financing_cost = overall_avg_inventory * (interest_rate / 100) * unit_cost

    st.subheader("Inventory Financing Results")
    st.write(f"Total Safety Stock: {total_safety_stock:.0f} units")
    st.write(f"Average Inventory Level: {total_avg_inventory:.0f} units")
    st.write(f"Inventory Financing Cost (per year): {financing_cost:.0f}")

# =============================================================================
# Submission
# =============================================================================
if st.button("Submit Data"):
    st.write("Data submitted successfully!")
    st.write("Global Parameters:", {"interest_rate": interest_rate, "service_level": service_level, "layout_type": layout_type, "shipping_cost_rate": shipping_cost_rate, "unit_cost": unit_cost})
    st.write("Market Area Data:", market_area_data)
    st.write("Warehouse Data:", warehouse_data)

