import pandas as pd
import numpy as np
import statsmodels.api as sm
from scipy import stats
import seaborn as sns
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')

print("=" * 70)
print("PRADA GROUP FULL FUNNEL ANALYTICS PIPELINE")
print("=" * 70)


# 1. LOAD DATASETS


print("\nLoading datasets...\n")

df_top = pd.read_csv('top_funnel_prada_2025.csv')
df_mid = pd.read_csv('mid_funnel_prada_2025.csv')
df_bot = pd.read_csv('bottom_funnel_prada_2025.csv')

paid_social_platforms = ['Instagram', 'TikTok', 'YouTube', 'X']


# 2. TOP FUNNEL KPIs

df_top['CTR (%)'] = (df_top['Clicks'] / df_top['Impressions'].replace(0, np.nan)) * 100

df_top['ER (%)'] = np.where(
    df_top['Platform'].isin(paid_social_platforms),
    (df_top['Total_Engagements'] / df_top['Impressions'].replace(0, np.nan)) * 100,
    np.nan
)

df_top['Traffic_Source'] = df_top['Campaign_Category']


# 3. CROSS FUNNEL MERGE


print("Merging datasets...\n")

df_merged = pd.merge(
    df_mid,
    df_top[['Campaign_ID', 'Platform', 'Campaign_Category', 'Campaign_Type', 'Campaign_Ad_Spend', 'Impressions', 'Clicks', 'Total_Engagements']],
    on='Campaign_ID',
    how='left'
)

df_merged = pd.merge(
    df_merged,
    df_bot[['Customer_ID', 'Customer_Type', 'New_Customers_Acquired', 'Returning_Customers', 'Total_Marketing_Spend', 'Historical_Ecom_Lifetime_Value', 'Historical_AOV']],
    on='Customer_ID',
    how='left'
)


# 4. FRACTIONAL CUSTOMER ALLOCATION (Anonimlik Korumalı)


print("Applying customer allocation logic...\n")

df_identified = df_merged[df_merged['Customer_ID'].notnull()].copy()
df_anonymous = df_merged[df_merged['Customer_ID'].isnull()].copy()

customer_session_counts = df_identified.groupby('Customer_ID')['Session_ID'].transform('count').replace(0, 1)

df_identified['Allocated_New_Customers'] = df_identified['New_Customers_Acquired'] / customer_session_counts
df_identified['Allocated_Returning_Customers'] = df_identified['Returning_Customers'] / customer_session_counts
df_identified['Allocated_Total_Marketing_Spend'] = df_identified['Total_Marketing_Spend'] / customer_session_counts

df_identified['Returning_Transactions'] = np.where((df_identified['Transactions'] == 1) & (df_identified['Customer_Type'] == 'Returning'), 1, 0)
df_identified['New_Customer_Transactions'] = np.where((df_identified['Transactions'] == 1) & (df_identified['Customer_Type'] == 'New'), 1, 0)

for col in ['Allocated_New_Customers', 'Allocated_Returning_Customers', 'Allocated_Total_Marketing_Spend', 'Returning_Transactions', 'New_Customer_Transactions']:
    df_anonymous[col] = 0

df_merged = pd.concat([df_identified, df_anonymous])


# 5. MASTER AGGREGATION TABLE

print("Creating master aggregation table...\n")

group_cols = ['Region', 'Traffic_Source', 'Platform', 'Campaign_Category', 'Campaign_Type']

for col in ['Platform', 'Campaign_Category', 'Campaign_Type']:
    df_merged[col] = df_merged[col].fillna('None')
    df_top[col] = df_top[col].fillna('None')

mid_agg = df_merged.groupby(group_cols).agg({
    'Website_Sessions': 'sum',
    'Bounces': 'sum',
    'Add_To_Cart_Events': 'sum',
    'Transactions': 'sum',
    'Total_Revenue': 'sum',
    'Returning_Transactions': 'sum',
    'New_Customer_Transactions': 'sum'
}).reset_index()

bot_agg = df_merged.groupby(group_cols).agg({
    'Allocated_New_Customers': 'sum',
    'Allocated_Returning_Customers': 'sum',
    'Allocated_Total_Marketing_Spend': 'sum',
    'Historical_Ecom_Lifetime_Value': 'mean',
    'Historical_AOV': 'mean'
}).reset_index()

# Getting Top Funnel Spends directly from df_top'tan 
top_agg = df_top.groupby(group_cols).agg({
    'Campaign_Ad_Spend': 'sum',
    'Impressions': 'sum',
    'Clicks': 'sum',
    'Total_Engagements': 'sum'
}).reset_index()

master_agg = pd.merge(mid_agg, top_agg, on=group_cols, how='left')
master_agg = pd.merge(master_agg, bot_agg, on=group_cols, how='left')
master_agg = master_agg.fillna(0)


# 6. KPI CALCULATIONS

print("Calculating KPIs...\n")

master_agg['CTR (%)'] = np.where(
    master_agg['Traffic_Source'].isin(['Direct', 'Organic Search']),
    np.nan,
    (master_agg['Clicks'] / master_agg['Impressions'].replace(0, np.nan)) * 100
)

master_agg['ER (%)'] = np.where(
    master_agg['Traffic_Source'] == 'Paid Social Media',
    (master_agg['Total_Engagements'] / master_agg['Impressions'].replace(0, np.nan)) * 100,
    np.nan
)

master_agg['Bounce_Rate (%)'] = (master_agg['Bounces'] / master_agg['Website_Sessions'].replace(0, np.nan)) * 100
master_agg['Conversion_Rate (%)'] = (master_agg['Transactions'] / master_agg['Website_Sessions'].replace(0, np.nan)) * 100
master_agg['Cart_Abandonment_Rate (%)'] = ((master_agg['Add_To_Cart_Events'] - master_agg['Transactions']) / master_agg['Add_To_Cart_Events'].replace(0, np.nan)) * 100

master_agg['AOV ($)'] = master_agg['Total_Revenue'] / master_agg['Transactions'].replace(0, np.nan)
master_agg['Returning_Customer_Ratio (%)'] = (master_agg['Returning_Transactions'] / master_agg['Transactions'].replace(0, np.nan)) * 100

master_agg['CAC ($)'] = master_agg['Allocated_Total_Marketing_Spend'] / master_agg['Allocated_New_Customers'].replace(0, np.nan)
master_agg['Campaign_CAC ($)'] = master_agg['Campaign_Ad_Spend'] / master_agg['New_Customer_Transactions'].replace(0, np.nan)

no_roi_sources = ['Organic Search', 'Direct']
master_agg['Campaign_ROI (%)'] = np.where(
    master_agg['Traffic_Source'].isin(no_roi_sources),
    np.nan,
    ((master_agg['Total_Revenue'] - master_agg['Campaign_Ad_Spend']) / master_agg['Campaign_Ad_Spend'].replace(0, np.nan)) * 100
)

master_agg['CLV ($)'] = master_agg['Historical_Ecom_Lifetime_Value']
master_agg = master_agg.round(2)

master_agg.to_csv('master_funnel_summary.csv', index=False)
print("Master table exported.")


# 7. GLOBAL KPI SUMMARY

print("\n" + "=" * 70)
print("GLOBAL KPI SUMMARY")
print("=" * 70)

global_summary = pd.DataFrame({
    'Metric': [
        'Returning Customer Ratio (%)',
        'CAC ($)',
        'Campaign CAC ($)',
        'CLV ($)',
        'Bounce Rate (%)',
        'Cart Abandonment Rate (%)',
        'AOV ($)',
        'Conversion Rate (%)',
        'CTR (%) (Eligible Channels)',
        'ER (%) (Paid Social Only)',
        'Campaign ROI (%) (Eligible Channels)'
    ],
    'Value': [
        (df_merged['Returning_Transactions'].sum() / df_merged['Transactions'].replace(0, np.nan).sum()) * 100,
        (df_bot['Total_Marketing_Spend'].sum() / df_bot['New_Customers_Acquired'].replace(0, np.nan).sum()),
        (df_top['Campaign_Ad_Spend'].sum() / df_merged['New_Customer_Transactions'].replace(0, np.nan).sum()),
        df_bot['Historical_Ecom_Lifetime_Value'].mean(),
        (df_mid['Bounces'].sum() / df_mid['Website_Sessions'].replace(0, np.nan).sum()) * 100,
        ((df_mid['Add_To_Cart_Events'].sum() - df_mid['Transactions'].sum()) / df_mid['Add_To_Cart_Events'].replace(0, np.nan).sum()) * 100,
        (df_mid['Total_Revenue'].sum() / df_mid['Transactions'].replace(0, np.nan).sum()),
        (df_mid['Transactions'].sum() / df_mid['Website_Sessions'].replace(0, np.nan).sum()) * 100,
        (master_agg[master_agg['CTR (%)'].notnull()]['Clicks'].sum() / master_agg[master_agg['CTR (%)'].notnull()]['Impressions'].replace(0, np.nan).sum()) * 100,
        (master_agg[master_agg['ER (%)'].notnull()]['Total_Engagements'].sum() / master_agg[master_agg['ER (%)'].notnull()]['Impressions'].replace(0, np.nan).sum()) * 100,
        ((master_agg[master_agg['Campaign_ROI (%)'].notnull()]['Total_Revenue'].sum() - master_agg[master_agg['Campaign_ROI (%)'].notnull()]['Campaign_Ad_Spend'].sum()) / master_agg[master_agg['Campaign_ROI (%)'].notnull()]['Campaign_Ad_Spend'].replace(0, np.nan).sum()) * 100
    ]
})

print(global_summary.round(2))


# 8. REGIONAL KPI SUMMARY

print("\n" + "=" * 70)
print("REGIONAL KPI SUMMARY")
print("=" * 70)

regional_summary = master_agg.groupby('Region').agg({
    'Returning_Transactions': 'sum',
    'Transactions': 'sum',
    'Allocated_Total_Marketing_Spend': 'sum',
    'Allocated_New_Customers': 'sum',
    'Campaign_Ad_Spend': 'sum',
    'New_Customer_Transactions': 'sum',
    'CLV ($)': 'mean',
    'Bounces': 'sum',
    'Website_Sessions': 'sum',
    'Add_To_Cart_Events': 'sum',
    'Total_Revenue': 'sum'
})

regional_ctr = master_agg[master_agg['CTR (%)'].notnull()].groupby('Region').apply(lambda x: (x['Clicks'].sum() / x['Impressions'].replace(0, np.nan).sum()) * 100)
regional_er = master_agg[master_agg['ER (%)'].notnull()].groupby('Region').apply(lambda x: (x['Total_Engagements'].sum() / x['Impressions'].replace(0, np.nan).sum()) * 100)
regional_roi = master_agg[master_agg['Campaign_ROI (%)'].notnull()].groupby('Region').apply(lambda x: ((x['Total_Revenue'].sum() - x['Campaign_Ad_Spend'].sum()) / x['Campaign_Ad_Spend'].replace(0, np.nan).sum()) * 100)

regional_summary['Returning_Customer_Ratio (%)'] = (regional_summary['Returning_Transactions'] / regional_summary['Transactions'].replace(0, np.nan)) * 100
regional_summary['CAC ($)'] = (regional_summary['Allocated_Total_Marketing_Spend'] / regional_summary['Allocated_New_Customers'].replace(0, np.nan))
regional_summary['Campaign_CAC ($)'] = (regional_summary['Campaign_Ad_Spend'] / regional_summary['New_Customer_Transactions'].replace(0, np.nan))
regional_summary['Bounce_Rate (%)'] = (regional_summary['Bounces'] / regional_summary['Website_Sessions'].replace(0, np.nan)) * 100
regional_summary['Cart_Abandonment_Rate (%)'] = ((regional_summary['Add_To_Cart_Events'] - regional_summary['Transactions']) / regional_summary['Add_To_Cart_Events'].replace(0, np.nan)) * 100
regional_summary['AOV ($)'] = (regional_summary['Total_Revenue'] / regional_summary['Transactions'].replace(0, np.nan))
regional_summary['Conversion_Rate (%)'] = (regional_summary['Transactions'] / regional_summary['Website_Sessions'].replace(0, np.nan)) * 100

regional_summary['CTR (%)'] = regional_ctr
regional_summary['ER (%)'] = regional_er
regional_summary['Campaign_ROI (%)'] = regional_roi

print(regional_summary.round(2)[['Returning_Customer_Ratio (%)', 'CAC ($)', 'Bounce_Rate (%)', 'Cart_Abandonment_Rate (%)', 'AOV ($)', 'Conversion_Rate (%)', 'CTR (%)', 'ER (%)', 'Campaign_ROI (%)']])


# 9. AUTOMATED INSIGHT SCANNER

print("\n" + "=" * 70)
print("SCANNING DATA FOR EXECUTIVE INSIGHTS TABLE...")
print("=" * 70)

metrics = [
    'Website_Sessions', 'Returning_Customer_Ratio (%)', 'CAC ($)', 'CLV ($)', 
    'Bounce_Rate (%)', 'Cart_Abandonment_Rate (%)', 'AOV ($)', 
    'Conversion_Rate (%)', 'CTR (%)', 'ER (%)', 'Campaign_ROI (%)'
]

insights_data = []

def scan_best_worst_to_table(df, metric, dimension, scope, category):
    # Sıfır veya NaN olan ölü veriler rapora "En Kötü" olarak düşmez
    valid_df = df[df[metric].notnull() & (df[metric] > 0)].copy()
    valid_df = valid_df[(valid_df[dimension] != 'None') & (valid_df[dimension] != 0)]
    
    if valid_df.empty:
        return

    analysis = valid_df.groupby(dimension)[metric].mean().reset_index().sort_values(metric, ascending=False)
    if len(analysis) == 0:
        return
        
    top = analysis.iloc[0]
    lowest = analysis.iloc[-1]
    
    insights_data.append({
        'Scope': scope,
        'Category': category,
        'Metric': metric,
        'Top_Performer': top[dimension],
        'Top_Value': round(top[metric], 2),
        'Lowest_Performer': lowest[dimension],
        'Lowest_Value': round(lowest[metric], 2)
    })

for metric in metrics:
    scan_best_worst_to_table(master_agg, metric, 'Traffic_Source', 'Global', 'Traffic Source')
    scan_best_worst_to_table(master_agg, metric, 'Platform', 'Global', 'Platform')
    scan_best_worst_to_table(master_agg, metric, 'Campaign_Category', 'Global', 'Campaign Category')
    scan_best_worst_to_table(master_agg, metric, 'Campaign_Type', 'Global', 'Campaign Type')

for region in master_agg['Region'].unique():
    if region == 'None': continue
    region_df = master_agg[master_agg['Region'] == region]
    for metric in metrics:
        scan_best_worst_to_table(region_df, metric, 'Traffic_Source', region, 'Traffic Source')
        scan_best_worst_to_table(region_df, metric, 'Platform', region, 'Platform')
        scan_best_worst_to_table(region_df, metric, 'Campaign_Category', region, 'Campaign Category')
        scan_best_worst_to_table(region_df, metric, 'Campaign_Type', region, 'Campaign Type')

pd.DataFrame(insights_data).to_csv('executive_insights_report.csv', index=False)
print("--> SUCCESS: 'executive_insights_report.csv' created!\n")


# 10. CORRELATION ANALYSIS

print("=" * 70)
print("CORRELATION ANALYSIS")
print("=" * 70)

campaign_corr_df = (
    df_merged[df_merged['Campaign_ID'].notnull()]
    .groupby('Campaign_ID')
    .agg({
        'Impressions': 'max',
        'Clicks': 'max',
        'Total_Engagements': 'max',
        'Campaign_Ad_Spend': 'max',
        'Website_Sessions': 'sum',
        'Transactions': 'sum',
        'Total_Revenue': 'sum',
        'Traffic_Source': 'first'
    })
)

campaign_corr_df['CTR'] = np.where(campaign_corr_df['Traffic_Source'].str.contains('Direct', case=False, na=False), np.nan, (campaign_corr_df['Clicks'] / campaign_corr_df['Impressions']) * 100)
campaign_corr_df['ER'] = np.where(campaign_corr_df['Traffic_Source'].str.contains('Paid Social', case=False, na=False), (campaign_corr_df['Total_Engagements'] / campaign_corr_df['Impressions']) * 100, np.nan)
campaign_corr_df['Conversion_Rate'] = (campaign_corr_df['Transactions'] / campaign_corr_df['Website_Sessions']) * 100
campaign_corr_df['Campaign_ROI'] = np.where(campaign_corr_df['Traffic_Source'].str.contains('Organic|Direct', case=False, na=False), np.nan, ((campaign_corr_df['Total_Revenue'] - campaign_corr_df['Campaign_Ad_Spend']) / campaign_corr_df['Campaign_Ad_Spend']) * 100)

corr_matrix = campaign_corr_df[['CTR', 'ER', 'Conversion_Rate', 'Campaign_ROI']].corr()
print(corr_matrix.round(3))


# 11. MULTIPLE LINEAR REGRESSION

print("\n" + "=" * 70)
print("MULTIPLE LINEAR REGRESSION")
print("=" * 70)
print("\nModel: Cross-Funnel Drivers of Revenue")

regression_df = (
    df_merged[df_merged['Campaign_ID'].notnull()]
    .groupby('Campaign_ID')
    .agg({
        'Website_Sessions': 'sum',
        'Bounces': 'sum',
        'Add_To_Cart_Events': 'sum',
        'Transactions': 'sum',
        'Total_Revenue': 'sum',
        'Impressions': 'max',
        'Clicks': 'max',
        'Total_Engagements': 'max',
        'Traffic_Source': 'first'
    })
    .reset_index()
)

regression_df['CTR'] = np.where(regression_df['Traffic_Source'].str.contains('Direct', case=False, na=False), 0, (regression_df['Clicks'] / regression_df['Impressions'].replace(0, np.nan)) * 100)
regression_df['ER'] = np.where(regression_df['Traffic_Source'].str.contains('Paid Social', case=False, na=False), (regression_df['Total_Engagements'] / regression_df['Impressions'].replace(0, np.nan)) * 100, 0)
regression_df['Bounce_Rate'] = (regression_df['Bounces'] / regression_df['Website_Sessions'].replace(0, np.nan)) * 100
regression_df['Conversion_Rate'] = (regression_df['Transactions'] / regression_df['Website_Sessions'].replace(0, np.nan)) * 100
regression_df = regression_df.fillna(0)

X = regression_df[['CTR', 'ER', 'Bounce_Rate', 'Conversion_Rate']]
y = regression_df['Total_Revenue']
X = sm.add_constant(X)
model = sm.OLS(y, X).fit()

print(model.summary())


# 12. ANOVA: REGIONAL CAC DIFFERENCES


print("\n" + "=" * 70)
print("ANOVA: REGIONAL INDIVIDUAL CAC DIFFERENCES")
print("=" * 70)

new_customers = df_bot[df_bot['Customer_Type'] == 'New'].copy()
new_customers['Individual_CAC'] = new_customers['Total_Marketing_Spend']

na_cac = new_customers[new_customers['Region'] == 'North America']['Individual_CAC']
eu_cac = new_customers[new_customers['Region'] == 'Europe']['Individual_CAC']
apac_cac = new_customers[new_customers['Region'] == 'APAC']['Individual_CAC']

f_stat, p_value = stats.f_oneway(na_cac, eu_cac, apac_cac)

print(f"F-Statistic: {f_stat:.3f}")
print(f"P-Value: {p_value:.6e}")
if p_value < 0.05:
    print("Conclusion: There is a statistically significant difference in CAC across regions (p < 0.05).")
else:
    print("Conclusion: No statistically significant difference in CAC across regions.")


# 13. VISUALIZATIONS

print("\nGenerating visualizations...\n")

plt.figure(figsize=(8, 6))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, fmt=".2f")
plt.title("Cross Funnel Correlation Heatmap (Prada Group)")
plt.tight_layout()
plt.savefig('cross_funnel_heatmap.png', dpi=300)
plt.close()

plt.figure(figsize=(8, 6))
sns.boxplot(x='Region', y='Total_Marketing_Spend', data=new_customers, palette='Set2')
plt.title("Regional CAC Distribution (Prada Group)")
plt.tight_layout()
plt.savefig('anova_cac_boxplot.png', dpi=300)
plt.close()

print("Visualizations exported.\n")

# 14. EXPORT ADDITIONAL REPORTS

regional_summary.to_csv('regional_kpi_summary.csv') 
global_summary.to_csv('global_kpi_summary.csv', index=False)

print("=" * 70)
print("PIPELINE COMPLETED SUCCESSFULLY")
print("=" * 70)