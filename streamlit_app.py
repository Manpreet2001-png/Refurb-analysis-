import streamlit as st
import pandas as pd

# ------------------------
# Page Config
# ------------------------
st.set_page_config(page_title="iPhone & Samsung Repair Dashboard", layout="wide")
st.title("📱 Repair Dashboard (Failed Devices Only)")

# ------------------------
# Step 1: Upload Files
# ------------------------
st.header("Step 1: Upload your files")
test_file = st.file_uploader("Upload Blackbelt Test Report", type=["xlsx", "csv"])
price_file = st.file_uploader("Upload Parts Price List", type=["xlsx", "csv"])

# ------------------------
# Step 2: Read Files
# ------------------------
def read_file(file):
    if file.name.endswith(".xlsx"):
        return pd.read_excel(file)
    else:
        return pd.read_csv(file)

if test_file and price_file:
    test_df = read_file(test_file)
    price_df = read_file(price_file)
    st.success("Files uploaded successfully ✅")

    # ------------------------
    # Step 3: Identify Columns
    # ------------------------
    imei_col = "IMEI/MEID"  # match your test sheet
    model_col = "Model"      # in test sheet
    failed_col = "Failed Test Summary"  # must contain failed parts

    # Check columns
    for col in [imei_col, model_col, failed_col]:
        if col not in test_df.columns:
            st.error(f"❌ Missing column in test report: {col}")
            st.stop()

    # Ensure pricing sheet has correct columns
    for col in ["MODEL", "PART", "PRICE"]:
        if col not in price_df.columns:
            st.error(f"❌ Missing column in pricing sheet: {col}")
            st.stop()

    # ------------------------
    # Step 4: Filter relevant rows
    # ------------------------
    test_df = test_df[[imei_col, model_col, failed_col]].dropna(subset=[failed_col])
    test_df[failed_col] = test_df[failed_col].astype(str)

    # Remove rows where failed_col is blank or PASS
    test_df = test_df[~test_df[failed_col].str.strip().str.upper().isin(["", "PASS"])]

    # ------------------------
    # Step 5: Explode multiple failed parts
    # ------------------------
    exploded_df = test_df.assign(Part=test_df[failed_col].str.split(r'\||,')).explode("Part")
    exploded_df["Part"] = exploded_df["Part"].str.strip()

    # ------------------------
    # Step 6: Merge with pricing
    # ------------------------
    merged_df = exploded_df.merge(price_df, left_on=[model_col, "Part"], right_on=["MODEL", "PART"], how="left")
    merged_df["PRICE"] = merged_df["PRICE"].fillna(0)

    # ------------------------
    # Step 7: Display Failed Parts & Costs
    # ------------------------
    display_cols = [imei_col, model_col, "Part", "PRICE"]
    st.subheader("Failed Devices & Costs")
    st.dataframe(merged_df[display_cols].reset_index(drop=True))

    # ------------------------
    # Step 8: Summary Stats
    # ------------------------
    total_cost = merged_df["PRICE"].sum()
    st.metric("💸 Total Repair Cost", f"£{total_cost}")

    cost_per_model = merged_df.groupby(model_col)["PRICE"].sum()
    st.subheader("Cost per Model")
    st.bar_chart(cost_per_model)

    # ------------------------
    # Step 9: Download CSV
    # ------------------------
    st.header("Download Processed Report")
    csv = merged_df[display_cols].to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", data=csv, file_name="failed_parts_cost.csv", mime="text/csv")

else:
    st.info("Upload both test report and pricing sheet to generate the dashboard 👆")
