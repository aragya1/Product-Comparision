import streamlit as st

st.title("AI-Powered Product Comparison")
keyword = st.text_input("Enter product keyword")
if st.button("Search"):
    # Trigger multi-agent workflow (domain classification, retrieval, etc.)
    results_df, summary = run_comparison_pipeline(keyword)  # custom function
    st.subheader("Comparison Table")
    st.table(results_df)       # Display DataFrame as table
    st.markdown("**AI Summary:** " + summary)
